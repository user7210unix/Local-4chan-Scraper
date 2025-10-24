"""
Settings manager for user preferences
"""

import json
from pathlib import Path
from threading import Lock

class SettingsManager:
    """Manages user settings"""
    
    DEFAULT_SETTINGS = {
        'theme': 'dark',
        'autoRefresh': False,
        'refreshInterval': 60,
        'enableDownloadButton': False,
        'showStickyThreads': True,
        'maxThreadsPerPage': 50,
        'imageHoverPreview': True,
        'compactView': False,
        'quickBoards': ['g', 'pol', 'v', 'tv', 'b', 'x']
    }
    
    def __init__(self, settings_file):
        self.settings_file = Path(settings_file)
        self.lock = Lock()
        self._ensure_file()
    
    def _ensure_file(self):
        """Create settings file if it doesn't exist"""
        if not self.settings_file.exists():
            self.save_settings(self.DEFAULT_SETTINGS)
    
    def get_settings(self):
        """Load settings from file"""
        with self.lock:
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults for any missing keys
                    return {**self.DEFAULT_SETTINGS, **settings}
            except Exception as e:
                print(f"⚠️  Failed to load settings: {e}")
                return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self, settings):
        """Save settings to file"""
        with self.lock:
            try:
                with open(self.settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)
                return True
            except Exception as e:
                print(f"❌ Failed to save settings: {e}")
                return False
    
    def get_setting(self, key, default=None):
        """Get a specific setting"""
        settings = self.get_settings()
        return settings.get(key, default)
    
    def set_setting(self, key, value):
        """Set a specific setting"""
        settings = self.get_settings()
        settings[key] = value
        return self.save_settings(settings)
