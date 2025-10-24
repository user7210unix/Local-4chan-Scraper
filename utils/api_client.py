"""
4chan API client with retry logic and rate limiting
"""

import time
import requests
from threading import Lock

class FourChanAPI:
    """4chan API client"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (4chan Local Scraper v2.0)'
        })
        self.last_request = 0
        self.rate_limit = 1.0  # seconds between requests
        self.lock = Lock()
    
    def _wait_rate_limit(self):
        """Enforce rate limiting"""
        with self.lock:
            elapsed = time.time() - self.last_request
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
            self.last_request = time.time()
    
    def _make_request(self, url, max_retries=3):
        """Make API request with retry logic"""
        self._wait_rate_limit()
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    return None
                print(f"⚠️  HTTP error {e.response.status_code}: {url}")
            except Exception as e:
                print(f"⚠️  Request failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return None
    
    def fetch_boards(self):
        """Fetch list of all boards"""
        url = "https://a.4cdn.org/boards.json"
        data = self._make_request(url)
        
        if data and 'boards' in data:
            return data['boards']
        return []
    
    def fetch_catalog(self, board):
        """Fetch catalog for a board"""
        url = f"https://a.4cdn.org/{board}/catalog.json"
        data = self._make_request(url)
        
        if not data:
            return []
        
        # Flatten catalog pages into single thread list
        threads = []
        for page in data:
            threads.extend(page.get('threads', []))
        
        return threads
    
    def fetch_thread(self, board, thread_id):
        """Fetch thread data"""
        url = f"https://a.4cdn.org/{board}/thread/{thread_id}.json"
        return self._make_request(url)
    
    def download_file(self, url, dest_path):
        """Download file (for user-initiated downloads)"""
        try:
            self._wait_rate_limit()
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = self.session.get(url, timeout=15, stream=True)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"❌ Download failed: {url} - {e}")
            if dest_path.exists():
                dest_path.unlink()
            return False
    
    def check_health(self):
        """Check if API is reachable"""
        try:
            response = self.session.get("https://a.4cdn.org/boards.json", timeout=5)
            return response.status_code == 200
        except:
            return False
