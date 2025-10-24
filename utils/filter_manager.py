"""
Thread filtering system - hide threads by keywords
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
        self.filters = self._load_filters()
    
    def _load_filters(self):
        """Load filters from file"""
        if not self.filters_file.exists():
            return {}
        
        try:
            with open(self.filters_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def _save_filters(self):
        """Save filters to file"""
        try:
            with open(self.filters_file, 'w') as f:
                json.dump(self.filters, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving filters: {e}")
            return False
    
    def get_board_filters(self, board):
        """Get all filters for a board"""
        with self.lock:
            return self.filters.get(board, [])
    
    def add_filter(self, board, filter_data):
        """Add a new filter for a board"""
        with self.lock:
            if board not in self.filters:
                self.filters[board] = []
            
            # Create filter object
            new_filter = {
                'id': len(self.filters[board]),
                'keyword': filter_data.get('keyword', ''),
                'type': filter_data.get('type', 'subject'),  # subject, comment, both
                'case_sensitive': filter_data.get('case_sensitive', False),
                'regex': filter_data.get('regex', False),
                'enabled': filter_data.get('enabled', True)
            }
            
            self.filters[board].append(new_filter)
            self._save_filters()
            
            return new_filter
    
    def remove_filter(self, board, filter_id):
        """Remove a filter from a board"""
        with self.lock:
            if board in self.filters:
                self.filters[board] = [f for f in self.filters[board] if f['id'] != filter_id]
                self._save_filters()
                return True
            return False
    
    def update_filter(self, board, filter_id, updates):
        """Update an existing filter"""
        with self.lock:
            if board in self.filters:
                for i, f in enumerate(self.filters[board]):
                    if f['id'] == filter_id:
                        self.filters[board][i].update(updates)
                        self._save_filters()
                        return True
            return False
    
    def apply_filters(self, threads, filters):
        """Apply filters to thread list"""
        if not filters:
            return threads
        
        filtered = []
        for thread in threads:
            should_hide = False
            
            for f in filters:
                if not f.get('enabled', True):
                    continue
                
                keyword = f['keyword']
                if not keyword:
                    continue
                
                # Get text to search
                filter_type = f.get('type', 'subject')
                if filter_type == 'subject':
                    text = thread.get('sub', '')
                elif filter_type == 'comment':
                    text = thread.get('com', '')
                else:  # both
                    text = thread.get('sub', '') + ' ' + thread.get('com', '')
                
                # Apply filter
                if f.get('regex', False):
                    # Regex matching
                    try:
                        flags = 0 if f.get('case_sensitive', False) else re.IGNORECASE
                        if re.search(keyword, text, flags):
                            should_hide = True
                            break
                    except re.error:
                        pass
                else:
                    # Simple substring matching
                    if f.get('case_sensitive', False):
                        if keyword in text:
                            should_hide = True
                            break
                    else:
                        if keyword.lower() in text.lower():
                            should_hide = True
                            break
            
            if not should_hide:
                filtered.append(thread)
        
        return filtered
    
    def clear_board_filters(self, board):
        """Clear all filters for a board"""
        with self.lock:
            if board in self.filters:
                del self.filters[board]
                self._save_filters()
                return True
            return False
    
    def get_all_filters(self):
        """Get filters for all boards"""
        with self.lock:
            return self.filters.copy()
    
    def import_filters(self, filters_data):
        """Import filters from external source"""
        with self.lock:
            try:
                self.filters = filters_data
                self._save_filters()
                return True
            except Exception as e:
                print(f"Error importing filters: {e}")
                return False
