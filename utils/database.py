"""
Database manager for caching API responses
"""

import json
import time
import sqlite3
from threading import Lock

class DatabaseManager:
    """Manages SQLite database for caching"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = Lock()
        self.cache_ttl = 600  # 10 minutes default
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            # Boards cache
            c.execute('''CREATE TABLE IF NOT EXISTS boards
                         (board TEXT PRIMARY KEY,
                          title TEXT,
                          is_worksafe INTEGER DEFAULT 0,
                          last_updated REAL)''')
            
            # Thread cache (stores full JSON)
            c.execute('''CREATE TABLE IF NOT EXISTS threads
                         (board TEXT,
                          thread_id INTEGER,
                          data TEXT,
                          last_updated REAL,
                          reply_count INTEGER DEFAULT 0,
                          PRIMARY KEY (board, thread_id))''')
            
            # Indexes
            c.execute('CREATE INDEX IF NOT EXISTS idx_threads_updated ON threads(last_updated)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_boards_updated ON boards(last_updated)')
            
            conn.commit()
            conn.close()
    
    def get_cached_boards(self, ignore_expiry=False):
        """Get cached boards list"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            c.execute('SELECT board, title, last_updated FROM boards ORDER BY board')
            rows = c.fetchall()
            conn.close()
            
            if not rows:
                return None
            
            # Check if cache is valid
            if not ignore_expiry:
                last_updated = rows[0]['last_updated']
                if not self._is_valid(last_updated, ttl=3600):  # 1 hour for boards
                    return None
            
            return [{'board': r['board'], 'title': r['title']} for r in rows]
    
    def cache_boards(self, boards):
        """Cache boards list"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            timestamp = time.time()
            c.execute('DELETE FROM boards')
            
            for board in boards:
                c.execute('''INSERT INTO boards (board, title, is_worksafe, last_updated)
                             VALUES (?, ?, ?, ?)''',
                          (board['board'], board['title'], board.get('ws_board', 0), timestamp))
            
            conn.commit()
            conn.close()
    
    def get_cached_thread(self, board, thread_id):
        """Get cached thread data"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            c.execute('SELECT data, last_updated FROM threads WHERE board=? AND thread_id=?',
                      (board, thread_id))
            row = c.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Check if cache is valid
            if not self._is_valid(row['last_updated'], ttl=self.cache_ttl):
                return None
            
            return json.loads(row['data'])
    
    def cache_thread(self, board, thread_id, thread_data):
        """Cache thread data"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            posts = thread_data.get('posts', [])
            reply_count = len(posts) - 1 if posts else 0
            
            c.execute('''REPLACE INTO threads (board, thread_id, data, last_updated, reply_count)
                         VALUES (?, ?, ?, ?, ?)''',
                      (board, thread_id, json.dumps(thread_data), time.time(), reply_count))
            
            conn.commit()
            conn.close()
    
    def clear_cache(self):
        """Clear all cached data"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            c.execute('DELETE FROM boards')
            c.execute('DELETE FROM threads')
            
            conn.commit()
            conn.close()
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            cutoff = time.time() - self.cache_ttl
            c.execute('DELETE FROM threads WHERE last_updated < ?', (cutoff,))
            
            deleted = c.rowcount
            conn.commit()
            conn.close()
            
            return deleted
    
    def get_stats(self):
        """Get database statistics"""
        with self.lock:
            conn = self._get_connection()
            c = conn.cursor()
            
            c.execute('SELECT COUNT(*) as count FROM boards')
            boards_count = c.fetchone()['count']
            
            c.execute('SELECT COUNT(*) as count FROM threads')
            threads_count = c.fetchone()['count']
            
            c.execute('SELECT SUM(reply_count) as total FROM threads')
            total_posts = c.fetchone()['total'] or 0
            
            conn.close()
            
            return {
                'boards': boards_count,
                'threads': threads_count,
                'total_posts': total_posts
            }
    
    def _is_valid(self, timestamp, ttl=None):
        """Check if timestamp is still valid"""
        if ttl is None:
            ttl = self.cache_ttl
        return (time.time() - timestamp) < ttl
