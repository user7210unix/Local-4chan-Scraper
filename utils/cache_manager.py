"""
Cache manager for temporary image storage
Only stores thumbnails by default - full images served on-demand
"""

import os
import time
import shutil
import requests
from pathlib import Path
from threading import Lock, Thread

class CacheManager:
    """Manages temporary cache for thumbnails and on-demand images"""
    
    def __init__(self, cache_dir, max_size_mb=500):
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.lock = Lock()
        self.download_queue = {}
        
        # Create cache structure
        self.thumbs_dir = self.cache_dir / 'thumbs'
        self.temp_images_dir = self.cache_dir / 'temp'
        
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Track access times for LRU cleanup
        self.access_times = {}
    
    def get_thumbnail(self, board, tim, async_download=False):
        """Get thumbnail from cache or download"""
        thumb_path = self.thumbs_dir / board / f"{tim}s.jpg"
        
        if thumb_path.exists():
            self._update_access_time(thumb_path)
            return thumb_path
        
        # Download thumbnail
        thumb_url = f"https://i.4cdn.org/{board}/{tim}s.jpg"
        
        if async_download:
            # Queue for background download
            self._queue_download(thumb_url, thumb_path)
            return None
        else:
            # Synchronous download
            return self._download_file(thumb_url, thumb_path)
    
    def get_image(self, board, tim, ext):
        """Get full image from temp cache or download on-demand"""
        image_path = self.temp_images_dir / board / f"{tim}{ext}"
        
        if image_path.exists():
            self._update_access_time(image_path)
            return image_path
        
        # Download full image to temp cache
        image_url = f"https://i.4cdn.org/{board}/{tim}{ext}"
        return self._download_file(image_url, image_path)
    
    def _download_file(self, url, dest_path):
        """Download file synchronously"""
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self._update_access_time(dest_path)
            self._check_cache_size()
            
            return dest_path
        except Exception as e:
            print(f"❌ Download failed: {url} - {e}")
            if dest_path.exists():
                dest_path.unlink()
            return None
    
    def _queue_download(self, url, dest_path):
        """Queue file for background download"""
        if str(dest_path) in self.download_queue:
            return
        
        self.download_queue[str(dest_path)] = True
        
        def download():
            self._download_file(url, dest_path)
            self.download_queue.pop(str(dest_path), None)
        
        Thread(target=download, daemon=True).start()
    
    def _update_access_time(self, file_path):
        """Update last access time for LRU"""
        with self.lock:
            self.access_times[str(file_path)] = time.time()
    
    def _check_cache_size(self):
        """Check cache size and cleanup if needed"""
        total_size = self._get_cache_size()
        
        if total_size > self.max_size_mb:
            self._cleanup_lru()
    
    def _get_cache_size(self):
        """Get total cache size in MB"""
        total = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.exists():
                    total += file_path.stat().st_size
        return total / (1024 * 1024)
    
    def _cleanup_lru(self):
        """Remove least recently used files until under limit"""
        with self.lock:
            # Get all cached files with access times
            files = []
            for root, dirs, filenames in os.walk(self.cache_dir):
                for filename in filenames:
                    file_path = Path(root) / filename
                    if file_path.exists():
                        access_time = self.access_times.get(str(file_path), 0)
                        size = file_path.stat().st_size
                        files.append((access_time, size, file_path))
            
            # Sort by access time (oldest first)
            files.sort(key=lambda x: x[0])
            
            # Remove files until under limit
            current_size = sum(f[1] for f in files) / (1024 * 1024)
            target_size = self.max_size_mb * 0.8  # Clean to 80% of limit
            
            for access_time, size, file_path in files:
                if current_size <= target_size:
                    break
                
                try:
                    file_path.unlink()
                    self.access_times.pop(str(file_path), None)
                    current_size -= size / (1024 * 1024)
                except Exception as e:
                    print(f"❌ Failed to delete {file_path}: {e}")
    
    def cleanup_expired(self, max_age_hours=24):
        """Remove files older than max_age_hours"""
        cutoff = time.time() - (max_age_hours * 3600)
        deleted = 0
        
        with self.lock:
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.exists():
                        access_time = self.access_times.get(str(file_path), 0)
                        if access_time < cutoff:
                            try:
                                file_path.unlink()
                                self.access_times.pop(str(file_path), None)
                                deleted += 1
                            except Exception:
                                pass
        
        return deleted
    
    def clear_all(self):
        """Clear all cached files"""
        with self.lock:
            for item in self.cache_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
            
            self.access_times.clear()
            
            # Recreate structure
            self.thumbs_dir.mkdir(parents=True, exist_ok=True)
            self.temp_images_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self):
        """Get cache statistics"""
        total_files = 0
        total_size = 0
        thumb_count = 0
        image_count = 0
        
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.exists():
                    total_files += 1
                    total_size += file_path.stat().st_size
                    
                    if 'thumbs' in str(file_path):
                        thumb_count += 1
                    else:
                        image_count += 1
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'thumbnails': thumb_count,
            'temp_images': image_count,
            'max_size_mb': self.max_size_mb
        }
