"""
Filter manager for hiding threads by keyword
"""

import json
import re
from pathlib import Path
from threading import Lock

class FilterManager:
    """Manages thread filters per board"""
    
    def __init__(self, filters_file):
        self.filters_file = Path(filters_file)
        self.lock = Lock()
        self._ensure_file()
    
    def _ensure_file(self):
        """Create filters file if it doesn't exist"""
        if not self.filters_file.exists():
            self.save_filters({})
    
    def get_all_filters(self):
        """Load all filters from file"""
        with self.lock:
            try:
                with open(self.filters_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load filters: {e}")
                return {}
    
    def save_filters(self, filters):
        """Save filters to file"""
        with self.lock:
            try:
                with open(self.filters_file, 'w') as f:
                    json.dump(filters, f, indent=2)
                return True
            except Exception as e:
                print(f"❌ Failed to save filters: {e}")
                return False
    
    def get_board_filters(self, board):
        """Get filters for a specific board"""
        all_filters = self.get_all_filters()
        return all_filters.get(board, [])
    
    def add_filter(self, board, filter_data):
        """Add filter for a board"""
        all_filters = self.get_all_filters()
        
        if board not in all_filters:
            all_filters[board] = []
        
        # Add unique ID if not present
        if 'id' not in filter_data:
            filter_data['id'] = len(all_filters[board]) + 1
        
        # Ensure required fields
        if 'keyword' not in filter_data or 'enabled' not in filter_data:
            return False
        
        all_filters[board].append(filter_data)
        return self.save_filters(all_filters)
    
    def remove_filter(self, board, filter_id):
        """Remove filter by ID"""
        all_filters = self.get_all_filters()
        
        if board in all_filters:
            all_filters[board] = [f for f in all_filters[board] if f.get('id') != filter_id]
            return self.save_filters(all_filters)
        
        return False
    
    def apply_filters(self, threads, filters):
        """Apply filters to thread list"""
        if not filters:
            return threads
        
        filtered = []
        
        for thread in threads:
            should_hide = False
            
            # Check each enabled filter
            for f in filters:
                if not f.get('enabled', True):
                    continue
                
                keyword = f.get('keyword', '').lower()
                if not keyword:
                    continue
                
                # Check subject
                subject = thread.get('sub', '').lower()
                if keyword in subject:
                    should_hide = True
                    break
                
                # Check comment/body
                comment = thread.get('com', '').lower()
                # Strip HTML tags for matching
                comment = re.sub(r'<[^>]+>', '', comment)
                if keyword in comment:
                    should_hide = True
                    break
            
            if not should_hide:
                filtered.append(thread)
        
        return filtered
    
    def clear_board_filters(self, board):
        """Clear all filters for a board"""
        all_filters = self.get_all_filters()
        
        if board in all_filters:
            all_filters[board] = []
            return self.save_filters(all_filters)
        
        return True
