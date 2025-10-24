"""
Configuration management for 4chan scraper
"""
import os
from pathlib import Path
class Config:
    """Application configuration"""

    def __init__(self):
        # Base directories
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / 'data'
        self.CACHE_DIR = self.DATA_DIR / 'cache'
        self.DOWNLOADS_DIR = self.DATA_DIR / 'downloads'
        self.TEMPLATES_DIR = self.BASE_DIR / 'templates'

        # Database
        self.DB_PATH = self.DATA_DIR / 'chan.db'

        # Settings files
        self.SETTINGS_FILE = self.DATA_DIR / 'settings.json'
        self.HISTORY_FILE = self.DATA_DIR / 'history.json'
        self.FILTERS_FILE = self.DATA_DIR / 'filters.json'

        # API endpoints
        self.BOARDS_API = "https://a.4cdn.org/boards.json"
        self.CATALOG_API = "https://a.4cdn.org/{board}/catalog.json"
        self.THREAD_API = "https://a.4cdn.org/{board}/thread/{thread_id}.json"
        self.IMAGE_URL = "https://i.4cdn.org/{board}/{tim}{ext}"
        self.THUMB_URL = "https://i.4cdn.org/{board}/{tim}s.jpg"

        # Cache settings
        self.CACHE_TIME = int(os.getenv('CACHE_TIME', 10))  # minutes
        self.MAX_CACHE_SIZE = int(os.getenv('MAX_CACHE_SIZE', 500))  # MB
        self.CACHE_CLEANUP_INTERVAL = 3600  # seconds

        # Server settings
        self.HOST = os.getenv('HOST', '127.0.0.1')
        self.PORT = int(os.getenv('PORT', 5000))
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

        # Request settings
        self.TIMEOUT = 10
        self.MAX_RETRIES = 3
        self.USER_AGENT = 'Mozilla/5.0 (4chan Local Scraper v2.0)'

        # Create directories
        for directory in [self.DATA_DIR, self.CACHE_DIR, 
                         self.DOWNLOADS_DIR, self.TEMPLATES_DIR]:
            directory.mkdir(exist_ok=True, parents=True)
