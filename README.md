<div align="center">

# 🗂️ Local 4chan Scraper

<!-- WIP badge (top, centered) -->
<p align="center">
  <img src="https://img.shields.io/badge/🚧%20work%20in%20progress-orange?style=for-the-badge&labelColor=1f2937">
</p>

<div align="left">

A self-hosted localhost web application for browsing 4chan boards with local caching, greentext detection, image previews, and reply hover functionality.

## ✨ Features

- **📋 Board Browsing**: View all available 4chan boards
- **🧵 Thread Listing**: Browse threads with reply/image counts
- **💬 Post Display**: Read posts with proper formatting
- **🟢 Greentext Detection**: Automatic highlighting of greentext (lines starting with `>`)
- **🔗 Reply Links**: Clickable `>>123456` links with hover previews
- **🖼️ Image Previews**: Hover over thumbnails to see larger previews
- **💾 Smart Caching**: SQLite database + file caching for fast loading
- **🌙 Dark Mode**: Easy-on-the-eyes dark interface
- **🔄 Auto-refresh**: Configurable cache expiration

## 📁 Project Structure

```
4chan-scraper/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Configuration file
├── templates/
│   └── index.html        # Frontend template
└── data/                 # Auto-created
    ├── chan.db           # SQLite database
    └── images/           # Cached images
        ├── g/
        ├── pol/
        └── ...
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip

### Setup Steps

1. **Clone or create the project directory**:
```bash
mkdir 4chan-scraper
cd 4chan-scraper
```

2. **Create the files**:
   - Copy `app.py` to the root directory
   - Create `templates/` folder and add `index.html`
   - Create `requirements.txt`
   - Create `.env` configuration file

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure settings** (optional):
   Edit `.env` to customize:
   - `CACHE_TIME`: Cache duration in minutes (default: 10)
   - `BOARDS`: Default boards to display (default: g,pol,v,a)

5. **Run the application**:
```bash
python app.py
```

6. **Open your browser**:
   Navigate to `http://localhost:5000`

## 🎮 Usage

### Basic Flow
1. **Select a board** from the grid (e.g., `/g/` - Technology)
2. **Browse threads** - see thread subjects, reply counts, and image counts
3. **Click a thread** to view all posts
4. **Interact with posts**:
   - Hover over `>>123456` links to preview quoted posts
   - Hover over image thumbnails to see larger previews
   - Click images to open full size
   - Greentext is automatically highlighted in green

### Navigation
- Use the **← Back** button to return to the previous view
- Use **🔄 Refresh Cache**
