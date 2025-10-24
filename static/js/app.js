// 4chan Local Scraper - Main Application Script

let currentBoard = null;
let currentBoardTitle = '';
let currentThread = null;
let postsData = {};
let viewStack = [];
let settings = {
    theme: 'dark',
    layout: 'normal',
    showUsernames: true,
    enableImageHover: true,
    enableReplyHover: true,
    enableTreeView: false,
    autoRefresh: false,
    refreshInterval: 60,
    sidebarAutoHide: true,
    enableDownloadButton: false,
    enableMascot: false,
    mascotUrl: '',
    mascotOpacity: 50
};
let autoRefreshInterval = null;
let history = [];
let filters = {};

// Initialize
init();

async function init() {
    console.log('Initializing app...');
    await loadSettings();
    loadBoards();
    loadHistory();
    loadCacheStats();
    setupSidebarBehavior();
}

// Settings Management
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();
        settings = { ...settings, ...data };
        applySettings();
    } catch (e) {
        console.error('Failed to load settings:', e);
        applySettings();
    }
}

function applySettings() {
    document.body.setAttribute('data-theme', settings.theme || 'dark');
    document.getElementById('themeSelect').value = settings.theme || 'dark';
    document.getElementById('layoutSelect').value = settings.layout || 'normal';
    document.getElementById('showUsernames').checked = settings.showUsernames !== false;
    document.getElementById('enableImageHover').checked = settings.enableImageHover !== false;
    document.getElementById('enableReplyHover').checked = settings.enableReplyHover !== false;
    document.getElementById('enableTreeView').checked = settings.enableTreeView === true;
    document.getElementById('autoRefresh').checked = settings.autoRefresh === true;
    document.getElementById('refreshInterval').value = settings.refreshInterval || 60;
    document.getElementById('sidebarAutoHide').checked = settings.sidebarAutoHide !== false;
    document.getElementById('enableDownloadButton').checked = settings.enableDownloadButton === true;
    document.getElementById('enableMascot').checked = settings.enableMascot === true;
    document.getElementById('mascotUrl').value = settings.mascotUrl || '';
    document.getElementById('mascotOpacity').value = settings.mascotOpacity || 50;
    document.getElementById('mascotOpacityValue').textContent = (settings.mascotOpacity || 50) + '%';

    const container = document.getElementById('mainContainer');
    if (settings.layout === 'wide') {
        container.classList.add('wide');
    } else {
        container.classList.remove('wide');
    }

    updateMascot();

    if (settings.autoRefresh) {
        startAutoRefresh();
    }
}

function saveSettings() {
    settings.theme = document.getElementById('themeSelect').value;
    settings.layout = document.getElementById('layoutSelect').value;
    settings.showUsernames = document.getElementById('showUsernames').checked;
    settings.enableImageHover = document.getElementById('enableImageHover').checked;
    settings.enableReplyHover = document.getElementById('enableReplyHover').checked;
    settings.enableTreeView = document.getElementById('enableTreeView').checked;
    settings.autoRefresh = document.getElementById('autoRefresh').checked;
    settings.refreshInterval = parseInt(document.getElementById('refreshInterval').value);
    settings.sidebarAutoHide = document.getElementById('sidebarAutoHide').checked;
    settings.enableDownloadButton = document.getElementById('enableDownloadButton').checked;
    settings.enableMascot = document.getElementById('enableMascot').checked;
    settings.mascotUrl = document.getElementById('mascotUrl').value;
    settings.mascotOpacity = parseInt(document.getElementById('mascotOpacity').value);

    fetch('/api/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(settings)
    }).then(() => {
        applySettings();
        showNotification('Settings saved!');
        closeSettings();
    });
}

function changeTheme() {
    document.body.setAttribute('data-theme', document.getElementById('themeSelect').value);
}

function changeLayout() {
    const layout = document.getElementById('layoutSelect').value;
    const container = document.getElementById('mainContainer');
    if (layout === 'wide') {
        container.classList.add('wide');
    } else {
        container.classList.remove('wide');
    }
}

function toggleAutoRefresh() {
    if (document.getElementById('autoRefresh').checked) {
        startAutoRefresh();
    } else {
        stopAutoRefresh();
    }
}

function startAutoRefresh() {
    stopAutoRefresh();
    const interval = (settings.refreshInterval || 60) * 1000;
    autoRefreshInterval = setInterval(() => {
        if (currentThread && currentBoard) {
            const scrollPos = window.scrollY;
            loadThread(currentBoard, currentThread, true).then(() => {
                window.scrollTo(0, scrollPos);
            });
        }
    }, interval);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Mascot Management
function toggleMascot() {
    updateMascot();
}

function updateMascotOpacity(value) {
    document.getElementById('mascotOpacityValue').textContent = value + '%';
    const mascot = document.getElementById('mascot');
    mascot.style.opacity = value / 100;
}

function updateMascot() {
    const mascot = document.getElementById('mascot');
    if (settings.enableMascot && settings.mascotUrl) {
        mascot.src = settings.mascotUrl;
        mascot.style.opacity = (settings.mascotOpacity || 50) / 100;
        mascot.classList.remove('hidden');
    } else {
        mascot.classList.add('hidden');
    }
}

// Sidebar Management
function setupSidebarBehavior() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    let sidebarTimeout = null;
    let isManuallyToggled = false;

    document.addEventListener('mousemove', (e) => {
        if (!settings.sidebarAutoHide || isManuallyToggled) return;

        clearTimeout(sidebarTimeout);

        if (e.clientX < 50) {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        } else if (e.clientX > 270) {
            sidebarTimeout = setTimeout(() => {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('expanded');
            }, 1500);
        }
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
}

// API Calls
async function loadBoards() {
    console.log('Loading boards...');
    try {
        const response = await fetch('/api/boards');
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const boards = await response.json();
        console.log('Loaded boards:', boards.length);
        
        if (!boards || boards.length === 0) {
            throw new Error('No boards returned from API');
        }
        
        const boardsList = document.getElementById('boardsList');
        const quickBoards = document.getElementById('quickBoards');
        boardsList.innerHTML = '';
        quickBoards.innerHTML = '';
        
        boards.forEach(board => {
            const card = document.createElement('div');
            card.className = 'board-card';
            card.onclick = () => loadCatalog(board.board, board.title);
            card.innerHTML = `
                <div class="board-name">/${board.board}/</div>
                <div>${escapeHtml(board.title)}</div>
            `;
            boardsList.appendChild(card);

            if (['g', 'pol', 'v', 'a', 'b', 'biz', 'fit', 'tv', 'vg'].includes(board.board)) {
                const quickItem = document.createElement('div');
                quickItem.className = 'board-item';
                quickItem.onclick = () => loadCatalog(board.board, board.title);
                quickItem.innerHTML = `<strong>/${board.board}/</strong> ${board.title}`;
                quickBoards.appendChild(quickItem);
            }
        });
        
        document.querySelector('#boardsView .loading').style.display = 'none';
        console.log('✅ Boards loaded successfully');
    } catch (error) {
        console.error('❌ Failed to load boards:', error);
        showError('Failed to load boards: ' + error.message);
        document.querySelector('#boardsView .loading').textContent = 'Failed to load boards. Check console.';
    }
}

async function loadCatalog(board, title) {
    currentBoard = board;
    currentBoardTitle = title;
    viewStack.push('boards');
    
    showView('threadsView');
    document.getElementById('boardTitle').textContent = `/${board}/ - ${title}`;
    document.querySelector('#threadsView .loading').style.display = 'block';
    document.getElementById('threadsList').innerHTML = '';
    
    try {
        const response = await fetch(`/api/catalog/${board}`);
        const threads = await response.json();
        
        const threadsList = document.getElementById('threadsList');
        
        threads.forEach(thread => {
            const item = document.createElement('div');
            item.className = 'thread-item';
            if (thread.sticky) item.classList.add('sticky');
            item.onclick = () => loadThread(board, thread.no);
            
            const sub = thread.sub ? escapeHtml(decodeHtml(thread.sub)) : 'No Subject';
            const com = thread.com ? stripHtml(decodeHtml(thread.com)).substring(0, 250) : '';
            
            let thumbHtml = '<div style="color: var(--text-muted);">No Image</div>';
            if (thread.tim && thread.ext) {
                thumbHtml = `<img src="/api/image/${board}/${thread.tim}s.jpg" alt="Thumb" loading="lazy" onerror="this.parentElement.innerHTML='<div style=\\'color: var(--text-muted)\\'>No Image</div>'">`;
            }
            
            const stickyLabel = thread.sticky ? '<strong style="color: #dc2626;">[STICKY]</strong> ' : '';
            const closedLabel = thread.closed ? '<strong style="color: #6b7280;">[CLOSED]</strong> ' : '';
            
            item.innerHTML = `
                <div class="thread-thumb">${thumbHtml}</div>
                <div class="thread-details">
                    <div class="thread-info">
                        ${stickyLabel}${closedLabel}
                        #${thread.no} | R: ${thread.replies || 0} | I: ${thread.images || 0}
                    </div>
                    <div class="thread-subject">${sub}</div>
                    <div class="thread-preview">${com}...</div>
                </div>
            `;
            threadsList.appendChild(item);
        });
        
        document.querySelector('#threadsView .loading').style.display = 'none';
    } catch (error) {
        showError('Failed to load catalog');
        document.querySelector('#threadsView .loading').style.display = 'none';
    }
}

async function loadThread(board, threadId, isRefresh = false) {
    const scrollPos = window.scrollY;
    currentThread = threadId;
    
    if (!isRefresh) {
        viewStack.push('threads');
        showView('threadView');
        document.querySelector('#threadView .loading').style.display = 'block';
        document.getElementById('postsList').innerHTML = '';
    }
    
    try {
        const response = await fetch(`/api/thread/${board}/${threadId}`);
        const data = await response.json();
        const posts = data.posts || [];
        
        postsData = {};
        const postReplies = {};
        
        posts.forEach(post => {
            postsData[post.no] = post;
            postReplies[post.no] = [];
        });

        posts.forEach(post => {
            const com = post.com || '';
            const matches = com.matchAll(/&gt;&gt;(\d+)/g);
            for (const match of matches) {
                const replyTo = match[1];
                if (postReplies[replyTo]) {
                    postReplies[replyTo].push(post.no);
                }
            }
        });

        const threadTitle = posts[0]?.sub ? decodeHtml(posts[0].sub) : `Thread #${threadId}`;
        document.getElementById('threadTitle').textContent = threadTitle;
        
        const postsList = document.getElementById('postsList');
        postsList.innerHTML = '';
        
        posts.forEach((post, index) => {
            const postDiv = createPostElement(post, board, index === 0, postReplies[post.no] || []);
            postsList.appendChild(postDiv);
        });
        
        attachEventListeners();
        
        if (isRefresh) {
            window.scrollTo(0, scrollPos);
        }
        
        document.querySelector('#threadView .loading').style.display = 'none';
    } catch (error) {
        showError('Failed to load thread');
        document.querySelector('#threadView .loading').style.display = 'none';
    }
}

function createPostElement(post, board, isOP, replies) {
    const postDiv = document.createElement('div');
    postDiv.className = 'post' + (isOP ? ' op' : '');
    if (settings.enableTreeView && !isOP && replies.length === 0) {
        postDiv.classList.add('tree-view');
    }
    postDiv.id = `post-${post.no}`;
    
    const date = new Date(post.time * 1000).toLocaleString();
    const username = settings.showUsernames ? escapeHtml(post.name || 'Anonymous') : 'Anonymous';
    
    let imageHtml = '';
    if (post.tim && post.ext) {
        const imgSrc = `/api/image/${board}/${post.tim}${post.ext}`;
        const thumbSrc = `/api/image/${board}/${post.tim}s.jpg`;
        const hoverAttr = settings.enableImageHover ? 
            `onmousemove="showImagePreview(event, '${imgSrc}')" onmouseleave="hideImagePreview()"` : '';
        
        const fileSize = post.fsize ? Math.round(post.fsize / 1024) + ' KB' : '';
        const dimensions = post.w && post.h ? `${post.w}x${post.h}` : '';
        const filename = post.filename ? escapeHtml(post.filename + post.ext) : '';
        
        let downloadBtn = '';
        if (settings.enableDownloadButton) {
            downloadBtn = `<a href="/api/download/${board}/${post.tim}${post.ext}" class="download-btn btn" download>Download</a>`;
        }
        
        imageHtml = `
            <div class="post-image">
                <div class="post-file-info">
                    File: ${filename} (${fileSize}, ${dimensions})${downloadBtn}
                </div>
                <a href="${imgSrc}" target="_blank">
                    <img src="${thumbSrc}" alt="Image" loading="lazy" ${hoverAttr}>
                </a>
            </div>
        `;
    }
    
    postDiv.innerHTML = `
        <div class="post-header">
            <span class="post-author">${username}</span>
            <span class="post-date">${date}</span>
            <a class="post-number" href="#post-${post.no}" onclick="return false;">#${post.no}</a>
        </div>
        ${imageHtml}
        <div class="post-content">${formatPost(post.com || '')}</div>
    `;
    
    return postDiv;
}

function formatPost(html) {
    if (!html) return '';
    
    html = decodeHtml(html);
    
    html = html.replace(/&gt;&gt;(\d+)/g, 
        '<a class="post-link" data-post="$1" href="#post-$1" onclick="return false;">&gt;&gt;$1</a>');
    
    html = html.split('<br>').map(line => {
        if (line.trim().startsWith('&gt;') && !line.includes('&gt;&gt;')) {
            return `<span class="greentext">${line}</span>`;
        }
        return line;
    }).join('<br>');
    
    return html;
}

function attachEventListeners() {
    if (!settings.enableReplyHover) return;
    
    document.querySelectorAll('.post-link').forEach(link => {
        link.addEventListener('mouseenter', showReplyPreview);
        link.addEventListener('mouseleave', hideReplyPreview);
    });
}

function showReplyPreview(e) {
    const postNum = e.target.dataset.post;
    const post = postsData[postNum];
    
    if (!post) return;
    
    const preview = document.createElement('div');
    preview.className = 'hover-preview';
    preview.id = 'replyPreview';
    
    const username = settings.showUsernames ? escapeHtml(post.name || 'Anonymous') : 'Anonymous';
    preview.innerHTML = `
        <div style="color: var(--text-muted); margin-bottom: 8px; font-size: 11px;">
            <strong>${username}</strong> #${post.no}
        </div>
        <div style="font-size: 12px;">${formatPost(post.com || 'No content').substring(0, 500)}</div>
    `;
    
    document.body.appendChild(preview);
    positionPreview(e, preview);
}

function hideReplyPreview() {
    const preview = document.getElementById('replyPreview');
    if (preview) preview.remove();
}

function showImagePreview(e, src) {
    hideImagePreview();
    
    const preview = document.createElement('div');
    preview.className = 'image-preview';
    preview.id = 'imagePreview';
    preview.innerHTML = `<img src="${src}" alt="Preview">`;
    
    document.body.appendChild(preview);
    positionPreview(e, preview);
}

function hideImagePreview() {
    const preview = document.getElementById('imagePreview');
    if (preview) preview.remove();
}

function positionPreview(e, element) {
    const padding = 20;
    let x = e.clientX + padding;
    let y = e.clientY + padding;
    
    element.style.left = x + 'px';
    element.style.top = y + 'px';
    
    setTimeout(() => {
        const rect = element.getBoundingClientRect();
        
        if (rect.right > window.innerWidth) {
            x = e.clientX - rect.width - padding;
        }
        if (rect.bottom > window.innerHeight) {
            y = e.clientY - rect.height - padding;
        }
        
        if (x < 0) x = padding;
        if (y < 0) y = padding;
        
        element.style.left = x + 'px';
        element.style.top = y + 'px';
    }, 10);
}

// View Management
function showView(viewId) {
    ['boardsView', 'threadsView', 'threadView'].forEach(id => {
        document.getElementById(id).classList.add('hidden');
    });
    document.getElementById(viewId).classList.remove('hidden');
    document.getElementById('backBtn').classList.remove('hidden');
    
    if (viewId === 'boardsView') {
        document.getElementById('backBtn').classList.add('hidden');
    }
}

function goBack() {
    const previous = viewStack.pop();
    
    if (previous === 'threads') {
        loadCatalog(currentBoard, currentBoardTitle);
    } else if (previous === 'boards') {
        showView('boardsView');
        document.getElementById('backBtn').classList.add('hidden');
        viewStack = [];
    }
}

function refreshView() {
    if (currentThread && currentBoard) {
        loadThread(currentBoard, currentThread, true);
    } else if (currentBoard) {
        loadCatalog(currentBoard, currentBoardTitle);
    } else {
        location.reload();
    }
}

// History Management
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        history = await response.json();
        displayHistory();
    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

function displayHistory() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '';
    
    if (history.length === 0) {
        historyList.innerHTML = '<div style="color: var(--text-muted); font-size: 11px;">No history</div>';
        return;
    }
    
    const recent = history.slice(-10).reverse();
    recent.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.onclick = () => loadThread(item.board, item.thread_id);
        historyItem.innerHTML = `
            <div class="board-tag">/${item.board}/</div>
            <div class="thread-title">${escapeHtml(item.title)}</div>
        `;
        historyList.appendChild(historyItem);
    });
}

function clearHistory() {
    if (!confirm('Clear all browsing history?')) return;
    
    fetch('/api/history/clear', { method: 'POST' })
        .then(() => {
            history = [];
            displayHistory();
            showNotification('History cleared');
        });
}

// Cache Stats
async function loadCacheStats() {
    try {
        const response = await fetch('/api/cache/stats');
        const stats = await response.json();
        
        const cacheInfo = document.getElementById('cacheInfo');
        cacheInfo.innerHTML = `
            <div>Cache: ${stats.cache.total_size_mb} MB</div>
            <div>Thumbs: ${stats.cache.thumbs_count}</div>
            <div>Images: ${stats.cache.images_count}</div>
            <div>Threads: ${stats.database.threads}</div>
        `;
    } catch (e) {
        console.error('Failed to load cache stats:', e);
    }
}

// Filter Management
function openFilters() {
    if (!currentBoard) {
        alert('Please select a board first');
        return;
    }
    
    document.getElementById('currentFilterBoard').textContent = `/${currentBoard}/`;
    loadFilters();
    document.getElementById('filtersModal').classList.add('active');
}

function closeFilters() {
    document.getElementById('filtersModal').classList.remove('active');
}

async function loadFilters() {
    if (!currentBoard) return;
    
    try {
        const response = await fetch(`/api/filters/${currentBoard}`);
        filters[currentBoard] = await response.json();
        displayFilters();
    } catch (e) {
        console.error('Failed to load filters:', e);
    }
}

function displayFilters() {
    const filtersList = document.getElementById('filtersList');
    const boardFilters = filters[currentBoard] || [];
    
    if (boardFilters.length === 0) {
        filtersList.innerHTML = '<div style="color: var(--text-muted); font-size: 11px;">No filters</div>';
        return;
    }
    
    filtersList.innerHTML = '';
    boardFilters.forEach(filter => {
        const filterItem = document.createElement('div');
        filterItem.className = 'filter-item';
        filterItem.innerHTML = `
            <div>
                <div class="filter-keyword">${escapeHtml(filter.keyword)}</div>
                <div style="font-size: 11px; color: var(--text-muted);">
                    ${filter.type} | ${filter.case_sensitive ? 'Case Sensitive' : 'Case Insensitive'}
                    ${filter.regex ? '| Regex' : ''}
                </div>
            </div>
            <div class="filter-actions">
                <button onclick="removeFilter(${filter.id})">Remove</button>
            </div>
        `;
        filtersList.appendChild(filterItem);
    });
}

async function addFilter() {
    const keyword = document.getElementById('newFilterKeyword').value.trim();
    if (!keyword) {
        alert('Please enter a keyword');
        return;
    }
    
    const filterData = {
        keyword: keyword,
        type: document.getElementById('newFilterType').value,
        case_sensitive: document.getElementById('newFilterCaseSensitive').checked,
        regex: document.getElementById('newFilterRegex').checked,
        enabled: true
    };
    
    try {
        await fetch(`/api/filters/${currentBoard}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(filterData)
        });
        
        document.getElementById('newFilterKeyword').value = '';
        document.getElementById('newFilterCaseSensitive').checked = false;
        document.getElementById('newFilterRegex').checked = false;
        
        await loadFilters();
        showNotification('Filter added');
    } catch (e) {
        showError('Failed to add filter');
    }
}

async function removeFilter(filterId) {
    try {
        await fetch(`/api/filters/${currentBoard}`, {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: filterId })
        });
        
        await loadFilters();
        showNotification('Filter removed');
    } catch (e) {
        showError('Failed to remove filter');
    }
}

// Modal Management
function openSettings() {
    document.getElementById('settingsModal').classList.add('active');
}

function closeSettings() {
    document.getElementById('settingsModal').classList.remove('active');
}

// Close modals on outside click
document.getElementById('settingsModal').addEventListener('click', (e) => {
    if (e.target.id === 'settingsModal') closeSettings();
});

document.getElementById('filtersModal').addEventListener('click', (e) => {
    if (e.target.id === 'filtersModal') closeFilters();
});

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function decodeHtml(html) {
    const txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
}

function stripHtml(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || div.innerText || '';
}

function showError(message) {
    const container = document.querySelector('.container');
    const error = document.createElement('div');
    error.className = 'error';
    error.textContent = message;
    container.prepend(error);
    setTimeout(() => error.remove(), 5000);
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeSettings();
        closeFilters();
    }
});

console.log('✅ app.js loaded successfully');
