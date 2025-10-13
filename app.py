"""
Enhanced 4chan Local Scraper Web Application
Features: History tracking, settings, thumbnails, improved UI
"""

import os
import json
import time
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
IMAGES_DIR = DATA_DIR / 'images'
THUMBS_DIR = DATA_DIR / 'thumbs'
DB_PATH = DATA_DIR / 'chan.db'
SETTINGS_FILE = DATA_DIR / 'settings.json'
HISTORY_FILE = DATA_DIR / 'history.json'

# Create directories
for directory in [DATA_DIR, IMAGES_DIR, THUMBS_DIR]:
    directory.mkdir(exist_ok=True)

# 4chan API endpoints
BOARDS_API = "https://a.4cdn.org/boards.json"
CATALOG_API = "https://a.4cdn.org/{board}/catalog.json"
THREAD_API = "https://a.4cdn.org/{board}/thread/{thread_id}.json"
IMAGE_URL = "https://i.4cdn.org/{board}/{tim}{ext}"
THUMB_URL = "https://i.4cdn.org/{board}/{tim}s.jpg"

# Configuration
CACHE_TIME = int(os.getenv('CACHE_TIME', 10))
DEFAULT_BOARDS = os.getenv('BOARDS', 'g,pol,v,a').split(',')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Database initialization
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS boards
                 (board TEXT PRIMARY KEY, title TEXT, last_updated REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS threads
                 (board TEXT, thread_id INTEGER, data TEXT, last_updated REAL,
                  PRIMARY KEY (board, thread_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (board TEXT, filename TEXT, local_path TEXT, is_thumb INTEGER,
                  PRIMARY KEY (board, filename, is_thumb))''')
    
    conn.commit()
    conn.close()

init_db()

# Settings management
def load_settings():
    """Load user settings from file"""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {
        'theme': 'dark',
        'layout': 'centered',
        'customColors': {},
        'showUsernames': True,
        'enableImageHover': True,
        'enableReplyHover': True,
        'enableTreeView': False,
        'autoRefresh': False,
        'refreshInterval': 60,
        'sidebarAutoHide': True,
        'useSymbols': 'unicode'
    }

def save_settings(settings):
    """Save user settings to file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# History management
def load_history():
    """Load browsing history"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    """Save browsing history"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history[-100:], f, indent=2)  # Keep last 100 entries

def add_to_history(board, thread_id, title, timestamp=None):
    """Add thread visit to history"""
    history = load_history()
    entry = {
        'board': board,
        'thread_id': thread_id,
        'title': title or 'No Subject',
        'timestamp': timestamp or time.time()
    }
    # Remove duplicates
    history = [h for h in history if not (h['board'] == board and h['thread_id'] == thread_id)]
    history.append(entry)
    save_history(history)

# Helper functions
def is_cache_valid(timestamp, cache_minutes=CACHE_TIME):
    """Check if cached data is still valid"""
    if not timestamp:
        return False
    return (time.time() - timestamp) < (cache_minutes * 60)

def fetch_json(url, timeout=10):
    """Fetch JSON from URL with error handling"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def download_file(url, save_path):
    """Download file to local path"""
    try:
        response = requests.get(url, timeout=15, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

# API Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/boards')
def get_boards():
    """Fetch and cache board list"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT board, title, last_updated FROM boards')
    cached = c.fetchall()
    
    if cached and is_cache_valid(cached[0][2]):
        boards = [{'board': b[0], 'title': b[1]} for b in cached]
        conn.close()
        return jsonify(boards)
    
    data = fetch_json(BOARDS_API)
    if not data:
        conn.close()
        return jsonify([]), 500
    
    boards = data.get('boards', [])
    timestamp = time.time()
    
    c.execute('DELETE FROM boards')
    for board in boards:
        c.execute('INSERT INTO boards VALUES (?, ?, ?)',
                  (board['board'], board['title'], timestamp))
    
    conn.commit()
    conn.close()
    
    return jsonify(boards)

@app.route('/api/catalog/<board>')
def get_catalog(board):
    """Fetch catalog (threads with previews) for a board"""
    url = CATALOG_API.format(board=board)
    data = fetch_json(url)
    
    if not data:
        return jsonify([]), 500
    
    threads = []
    for page in data:
        for thread in page.get('threads', []):
            # Extract thread info with thumbnails
            thread_info = {
                'no': thread['no'],
                'sub': thread.get('sub', ''),
                'com': thread.get('com', ''),
                'replies': thread.get('replies', 0),
                'images': thread.get('images', 0),
                'time': thread.get('time', 0),
                'tim': thread.get('tim'),
                'ext': thread.get('ext'),
                'tn_w': thread.get('tn_w', 125),
                'tn_h': thread.get('tn_h', 125)
            }
            
            # Download thumbnail if available
            if thread_info['tim'] and thread_info['ext']:
                download_thumbnail(board, thread_info['tim'])
            
            threads.append(thread_info)
    
    return jsonify(threads[:100])

@app.route('/api/thread/<board>/<int:thread_id>')
def get_thread(board, thread_id):
    """Fetch thread posts with caching"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT data, last_updated FROM threads WHERE board=? AND thread_id=?',
              (board, thread_id))
    cached = c.fetchone()
    
    if cached and is_cache_valid(cached[1], cache_minutes=5):
        conn.close()
        return cached[0], 200, {'Content-Type': 'application/json'}
    
    url = THREAD_API.format(board=board, thread_id=thread_id)
    data = fetch_json(url)
    
    if not data:
        conn.close()
        return jsonify({'error': 'Thread not found'}), 404
    
    posts = data.get('posts', [])
    
    # Download images and thumbnails
    for post in posts:
        if 'tim' in post and 'ext' in post:
            download_image(board, post['tim'], post['ext'])
            download_thumbnail(board, post['tim'])
    
    # Add to history
    thread_title = posts[0].get('sub', '') if posts else 'No Subject'
    add_to_history(board, thread_id, thread_title)
    
    json_data = json.dumps(data)
    timestamp = time.time()
    
    c.execute('REPLACE INTO threads VALUES (?, ?, ?, ?)',
              (board, thread_id, json_data, timestamp))
    conn.commit()
    conn.close()
    
    return json_data, 200, {'Content-Type': 'application/json'}

def download_thumbnail(board, tim):
    """Download thumbnail image"""
    filename = f"{tim}s.jpg"
    local_path = THUMBS_DIR / board
    local_path.mkdir(exist_ok=True)
    full_path = local_path / filename
    
    if full_path.exists():
        return
    
    url = THUMB_URL.format(board=board, tim=tim)
    download_file(url, full_path)

def download_image(board, tim, ext):
    """Download full image"""
    filename = f"{tim}{ext}"
    local_path = IMAGES_DIR / board
    local_path.mkdir(exist_ok=True)
    full_path = local_path / filename
    
    if full_path.exists():
        return
    
    url = IMAGE_URL.format(board=board, tim=tim, ext=ext)
    download_file(url, full_path)

@app.route('/images/<board>/<filename>')
def serve_image(board, filename):
    """Serve cached images"""
    image_path = IMAGES_DIR / board
    return send_from_directory(image_path, filename)

@app.route('/thumbs/<board>/<filename>')
def serve_thumb(board, filename):
    """Serve cached thumbnails"""
    thumb_path = THUMBS_DIR / board
    return send_from_directory(thumb_path, filename)

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Get or update settings"""
    if request.method == 'POST':
        settings = request.json
        save_settings(settings)
        return jsonify({'status': 'saved'})
    return jsonify(load_settings())

@app.route('/api/history')
def history():
    """Get browsing history"""
    return jsonify(load_history())

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear browsing history"""
    save_history([])
    return jsonify({'status': 'cleared'})

@app.route('/api/refresh')
def refresh_cache():
    """Force refresh all cached data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM boards')
    c.execute('DELETE FROM threads')
    conn.commit()
    conn.close()
    return jsonify({'status': 'cache cleared'})

if __name__ == '__main__':
    print("Starting Enhanced 4chan Local Scraper...")
    print(f"Open http://localhost:5000 in your browser")
    print(f"Cache time: {CACHE_TIME} minutes")
    app.run(debug=True, host='127.0.0.1', port=5000)
