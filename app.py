"""
Enhanced 4chan Local Scraper - Main Application
Optimized for speed, stability, and minimal storage footprint
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Import modular components
try:
    from utils.config import Config
    from utils.database import DatabaseManager
    from utils.cache_manager import CacheManager
    from utils.api_client import FourChanAPI
    from utils.settings_manager import SettingsManager
    from utils.history_manager import HistoryManager
    from utils.filter_manager import FilterManager
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all utils/*.py files are present")
    sys.exit(1)

# Initialize configuration
config = Config()
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600

# Initialize managers
try:
    db = DatabaseManager(config.DB_PATH)
    cache = CacheManager(config.CACHE_DIR, max_size_mb=config.MAX_CACHE_SIZE)
    api = FourChanAPI()
    settings_mgr = SettingsManager(config.SETTINGS_FILE)
    history_mgr = HistoryManager(config.HISTORY_FILE)
    filter_mgr = FilterManager(config.FILTERS_FILE)
    
    # Initialize database
    db.init_db()
    print("✅ All managers initialized successfully")
except Exception as e:
    print(f"❌ Initialization Error: {e}")
    sys.exit(1)

@app.route('/')
def index():
    """Serve main application page"""
    html_file = config.TEMPLATES_DIR / 'index.html'
    if html_file.exists():
        return html_file.read_text()
    return jsonify({'error': 'Template not found'}), 500

@app.route('/api/boards')
def get_boards():
    """Fetch and cache board list"""
    try:
        # Check cache first
        cached = db.get_cached_boards()
        if cached:
            print(f"✅ Returning {len(cached)} cached boards")
            return jsonify(cached)
        
        # Fetch from API
        print("📡 Fetching boards from 4chan API...")
        boards = api.fetch_boards()
        if not boards:
            # Return stale cache if API fails
            stale = db.get_cached_boards(ignore_expiry=True)
            if stale:
                print(f"⚠️ API failed, returning {len(stale)} stale boards")
                return jsonify(stale)
            print("❌ No boards available")
            return jsonify({'error': 'Failed to fetch boards'}), 500
        
        # Update cache
        db.cache_boards(boards)
        print(f"✅ Cached {len(boards)} boards")
        return jsonify(boards)
    except Exception as e:
        print(f"❌ Error in get_boards: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/<board>')
def get_catalog(board):
    """Fetch catalog with filtering support"""
    # Fetch catalog
    threads = api.fetch_catalog(board)
    if not threads:
        return jsonify({'error': 'Failed to fetch catalog'}), 500
    
    # Apply filters
    filters = filter_mgr.get_board_filters(board)
    if filters:
        threads = filter_mgr.apply_filters(threads, filters)
    
    # Pre-cache thumbnails for first 20 threads
    for thread in threads[:20]:
        if thread.get('tim'):
            cache.get_thumbnail(board, thread['tim'], async_download=True)
    
    return jsonify(threads)

@app.route('/api/thread/<board>/<int:thread_id>')
def get_thread(board, thread_id):
    """Fetch thread with smart caching"""
    # Check cache first
    cached = db.get_cached_thread(board, thread_id)
    if cached:
        # Add to history
        posts = cached.get('posts', [])
        title = posts[0].get('sub', 'No Subject') if posts else 'No Subject'
        history_mgr.add_entry(board, thread_id, title)
        return jsonify(cached)
    
    # Fetch from API
    thread_data = api.fetch_thread(board, thread_id)
    if not thread_data:
        return jsonify({'error': 'Thread not found'}), 404
    
    posts = thread_data.get('posts', [])
    
    # Pre-cache thumbnails only (not full images)
    for post in posts:
        if post.get('tim'):
            cache.get_thumbnail(board, post['tim'], async_download=True)
    
    # Cache thread data
    db.cache_thread(board, thread_id, thread_data)
    
    # Add to history
    title = posts[0].get('sub', 'No Subject') if posts else 'No Subject'
    history_mgr.add_entry(board, thread_id, title)
    
    return jsonify(thread_data)

@app.route('/api/image/<board>/<filename>')
def get_image(board, filename):
    """Serve or proxy images on-demand (no persistent storage)"""
    # Extract tim and ext from filename
    tim = filename.rsplit('.', 1)[0].replace('s', '')  # Remove 's' for thumbs
    ext = '.' + filename.rsplit('.', 1)[1]
    
    is_thumb = filename.endswith('s.jpg')
    
    if is_thumb:
        # Get thumbnail from cache
        file_path = cache.get_thumbnail(board, tim)
    else:
        # Get full image from cache (downloads if needed)
        file_path = cache.get_image(board, tim, ext)
    
    if file_path and file_path.exists():
        return send_from_directory(file_path.parent, file_path.name)
    
    return jsonify({'error': 'Image not found'}), 404

@app.route('/api/download/<board>/<filename>')
def download_image(board, filename):
    """Force download full image (if enabled in settings)"""
    settings = settings_mgr.get_settings()
    if not settings.get('enableDownloadButton', False):
        return jsonify({'error': 'Downloads disabled'}), 403
    
    # Extract tim and ext
    tim = filename.rsplit('.', 1)[0]
    ext = '.' + filename.rsplit('.', 1)[1]
    
    # Download to user's downloads folder (not cache)
    download_path = config.DOWNLOADS_DIR / board
    download_path.mkdir(parents=True, exist_ok=True)
    
    full_path = download_path / filename
    if not full_path.exists():
        url = config.IMAGE_URL.format(board=board, tim=tim, ext=ext)
        if not api.download_file(url, full_path):
            return jsonify({'error': 'Download failed'}), 500
    
    return send_from_directory(download_path, filename, as_attachment=True)

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Manage user settings"""
    if request.method == 'POST':
        if settings_mgr.save_settings(request.json):
            return jsonify({'status': 'saved'})
        return jsonify({'error': 'Failed to save'}), 500
    return jsonify(settings_mgr.get_settings())

@app.route('/api/history', methods=['GET', 'POST'])
def history():
    """Manage browsing history"""
    if request.method == 'POST':
        if history_mgr.save_history(request.json):
            return jsonify({'status': 'saved'})
        return jsonify({'error': 'Failed to save'}), 500
    return jsonify(history_mgr.get_history())

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear all browsing history"""
    history_mgr.clear()
    return jsonify({'status': 'cleared'})

@app.route('/api/filters/<board>', methods=['GET', 'POST', 'DELETE'])
def filters(board):
    """Manage thread filters per board"""
    if request.method == 'POST':
        filter_data = request.json
        filter_mgr.add_filter(board, filter_data)
        return jsonify({'status': 'added'})
    
    elif request.method == 'DELETE':
        filter_id = request.json.get('id')
        filter_mgr.remove_filter(board, filter_id)
        return jsonify({'status': 'removed'})
    
    return jsonify(filter_mgr.get_board_filters(board))

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache and database"""
    cache.clear_all()
    db.clear_cache()
    return jsonify({'status': 'cleared'})

@app.route('/api/cache/stats')
def cache_stats():
    """Get cache statistics"""
    stats = cache.get_stats()
    db_stats = db.get_stats()
    return jsonify({
        'cache': stats,
        'database': db_stats,
        'cache_size_mb': config.MAX_CACHE_SIZE,
        'cache_ttl_minutes': config.CACHE_TIME
    })

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '2.0.0',
        'cache_enabled': True,
        'api_reachable': api.check_health()
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

def cleanup_on_startup():
    """Cleanup old cache on startup"""
    print("🧹 Cleaning up old cache...")
    cache.cleanup_expired()
    print("✅ Cleanup complete")

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 4chan Local Scraper v2.0")
    print("=" * 70)
    print(f"📂 Cache directory: {config.CACHE_DIR}")
    print(f"💾 Cache size limit: {config.MAX_CACHE_SIZE}MB")
    print(f"⏱️  Cache TTL: {config.CACHE_TIME} minutes")
    print(f"🗄️  Database: {config.DB_PATH}")
    print(f"🌐 Server: http://127.0.0.1:{config.PORT}")
    print("=" * 70)
    print("📝 Features:")
    print("  • Smart caching (thumbnails only by default)")
    print("  • Thread filtering support")
    print("  • Automatic cache cleanup")
    print("  • History tracking")
    print("  • Optional image downloads")
    print("=" * 70)
    
    cleanup_on_startup()
    
    print("\n✅ Server ready! Press Ctrl+C to stop\n")
    
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        threaded=True
    )
