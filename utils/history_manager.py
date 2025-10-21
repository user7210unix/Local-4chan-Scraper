"""
History manager for tracking visited threads
"""

import json
import time
from pathlib import Path
from threading import Lock

class HistoryManager:
    """Manages browsing history"""
    
    def __init__(self, history_file, max_entries=50):
        self.history_file = Path(history_file)
        self.max_entries = max_entries
        self.lock = Lock()
        self._ensure_file()
    
    def _ensure_file(self):
        """Create history file if it doesn't exist"""
        if not self.history_file.exists():
            self.save_history([])
    
    def get_history(self):
        """Load history from file"""
        with self.lock:
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load history: {e}")
                return []
    
    def save_history(self, history):
        """Save history to file"""
        with self.lock:
            try:
                with open(self.history_file, 'w') as f:
                    json.dump(history, f, indent=2)
                return True
            except Exception as e:
                print(f"❌ Failed to save history: {e}")
                return False
    
    def add_entry(self, board, thread_id, title):
        """Add entry to history (most recent first)"""
        history = self.get_history()
        
        # Remove duplicate if exists
        history = [h for h in history if not (h['board'] == board and h['thread_id'] == thread_id)]
        
        # Add new entry at the beginning
        entry = {
            'board': board,
            'thread_id': thread_id,
            'title': title,
            'timestamp': time.time()
        }
        history.insert(0, entry)
        
        # Limit history size
        history = history[:self.max_entries]
        
        return self.save_history(history)
    
    def clear(self):
        """Clear all history"""
        return self.save_history([])
    
    def remove_entry(self, board, thread_id):
        """Remove specific entry from history"""
        history = self.get_history()
        history = [h for h in history if not (h['board'] == board and h['thread_id'] == thread_id)]
        return self.save_history(history)
