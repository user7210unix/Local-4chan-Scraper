<div align="left">

# 🗂️ Local 4chan Scraper

<!-- WIP badge (top, centered) -->
<p align="left">
  <img src="https://img.shields.io/badge/🚧%20work%20in%20progress-orange?style=for-the-badge&labelColor=1f2937">
</p>

<div align="left">

A fast, efficient, and stable 4chan browser with smart caching.

## Features

- **Smart Caching**: Only thumbnails are cached by default - full images loaded on-demand
- **No Bloat**: Temporary cache auto-cleans, no permanent storage bloat
- **Thread Filtering**: Hide threads by keyword per board
- **History Tracking**: Recent threads in sidebar
- **Optional Downloads**: Enable download button in settings if needed
- **Fast & Stable**: Rate-limited API requests, retry logic, LRU cache cleanup

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open browser to `http://127.0.0.1:5000`

## Project Structure

```
4chan-scraper/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (optional)
├── utils/
│   ├── config.py          # Configuration management
│   ├── database.py        # SQLite cache manager
│   ├── cache_manager.py   # Image cache manager
│   ├── api_client.py      # 4chan API client
│   ├── settings_manager.py # User settings
│   ├── history_manager.py  # Browsing history
│   └── filter_manager.py   # Thread filters
├── templates/
│   └── index.html         # Frontend UI
└── data/
    ├── cache/             # Temporary image cache (auto-cleanup)
    │   ├── thumbs/        # Thumbnail cache
    │   └── temp/          # On-demand full images
    ├── downloads/         # User downloads (optional)
    ├── chan.db            # SQLite database
    ├── settings.json      # User settings
    ├── history.json       # Browsing history
    └── filters.json       # Thread filters
```

## Configuration

Optional environment variables in `.env`:

```
CACHE_TIME=10          # Cache TTL in minutes
MAX_CACHE_SIZE=500     # Max cache size in MB
HOST=127.0.0.1
PORT=5000
DEBUG=False
```

## How It Works

### Smart Caching System

1. **Thumbnails**: Automatically cached when browsing catalogs
2. **Full Images**: Only loaded on-demand when clicked, stored in temp cache
3. **LRU Cleanup**: Least recently used files removed when cache limit reached
4. **Auto Expiry**: Old cache files auto-deleted after 24 hours
5. **No Bloat**: User doesn't accumulate unused files

### Todo
- [ ] Improve Wide ui (images are still centered)
- [ ] Add favorite boards to the sidepanel (currently only hardcoded for testing purposes)
 
### Download vs Cache

- **Cache**: Temporary, auto-managed, for browsing only
- **Downloads**: Permanent, user-initiated, stored separately (optional)

## Usage

### Browse Boards
- Click any board from the grid to view its catalog

### Thread Filtering
1. Open a board catalog
2. Click "Filters" in sidebar
3. Add keywords to hide threads containing that text
4. Filters are per-board and persistent

### Settings
- **Theme**: Light or dark mode
- **Download Button**: Enable to show download buttons on images
- **Show Sticky**: Toggle sticky thread visibility
- **Image Hover**: Enable hover previews (future)

### History
- Recently viewed threads appear in sidebar
- Click to quickly return to a thread
- Clear all history with "Clear" button

## Performance

- Smart rate limiting (1 req/sec to 4chan API)
- Automatic retry on failed requests
- Threaded background thumbnail downloads
- Efficient SQLite caching for API responses
- LRU cleanup prevents disk bloat

## Troubleshooting

**Images not loading?**
- Check your internet connection
- 4chan CDN might be slow - wait a few seconds

**Cache too large?**
- Reduce `MAX_CACHE_SIZE` in .env
- Click "Settings" → "Clear Cache"

**API errors?**
- Rate limiting active - wait a few seconds
- 4chan API might be down temporarily

## License

MIT License - Free to use and modify
