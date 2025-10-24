#!/usr/bin/env python3
"""
Test script to verify 4chan scraper setup
Run this before starting the main app
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import flask
        print("✅ Flask installed")
    except ImportError:
        print("❌ Flask not installed. Run: pip install flask")
        return False
    
    try:
        import requests
        print("✅ Requests installed")
    except ImportError:
        print("❌ Requests not installed. Run: pip install requests")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv installed")
    except ImportError:
        print("❌ Python-dotenv not installed. Run: pip install python-dotenv")
        return False
    
    return True

def test_structure():
    """Test if directory structure is correct"""
    print("\nTesting directory structure...")
    base = Path(__file__).parent
    
    required_files = [
        'app.py',
        'requirements.txt',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js',
        'utils/__init__.py',
        'utils/config.py',
        'utils/database.py',
        'utils/cache_manager.py',
        'utils/api_client.py',
        'utils/settings_manager.py',
        'utils/history_manager.py',
        'utils/filter_manager.py'
    ]
    
    all_present = True
    for file in required_files:
        file_path = base / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_present = False
    
    return all_present

def test_utils():
    """Test if utils can be imported"""
    print("\nTesting utils import...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.config import Config
        from utils.database import DatabaseManager
        from utils.cache_manager import CacheManager
        from utils.api_client import FourChanAPI
        from utils.settings_manager import SettingsManager
        from utils.history_manager import HistoryManager
        from utils.filter_manager import FilterManager
        print("✅ All utils modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import utils: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api():
    """Test if 4chan API is reachable"""
    print("\nTesting 4chan API connection...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.api_client import FourChanAPI
        api = FourChanAPI()
        if api.check_health():
            print("✅ 4chan API is reachable")
            return True
        else:
            print("⚠️ 4chan API not reachable (may be temporarily down)")
            return True  # Don't fail on this
    except Exception as e:
        print(f"❌ Failed to test API: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("4chan Scraper Setup Verification")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_imports),
        ("File Structure", test_structure),
        ("Utils Modules", test_utils),
        ("API Connection", test_api)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
        print()
    
    print("=" * 60)
    print("Test Results:")
    print("=" * 60)
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! You can run: python3 app.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
