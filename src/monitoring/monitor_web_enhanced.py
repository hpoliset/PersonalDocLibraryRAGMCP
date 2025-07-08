#!/usr/bin/env python3
"""
Enhanced web monitoring interface for Spiritual Library indexing
Shows detailed status, progress, and book listings
"""

from flask import Flask, render_template_string, jsonify, request
import json
import os
from datetime import datetime
import glob
from src.core.config import config
import math

app = Flask(__name__)

# Paths from config - use absolute paths to avoid working directory issues
DB_DIR = str(config.db_directory)
BOOKS_DIR = str(config.books_directory)
STATUS_FILE = os.path.join(DB_DIR, "index_status.json")
INDEX_FILE = os.path.join(DB_DIR, "book_index.json")  
FAILED_PDFS_FILE = os.path.join(DB_DIR, "failed_pdfs.json")
LOCK_FILE = "/tmp/spiritual_library_index.lock"

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Spiritual Library Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-idle { background: #10b981; }
        .status-indexing { 
            background: #f59e0b; 
            animation: pulse 1s infinite;
        }
        .status-paused { 
            background: #6366f1; 
        }
        .status-error { background: #ef4444; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #764ba2;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        
        .file-list {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #e5e7eb;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9em;
        }
        
        .file-item {
            padding: 5px 0;
            border-bottom: 1px solid #f3f4f6;
        }
        
        .timestamp {
            color: #9ca3af;
            font-size: 0.8em;
        }
        
        .lock-info {
            background: #fef3c7;
            border: 1px solid #fbbf24;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        
        .lock-stale {
            background: #fee2e2;
            border-color: #f87171;
        }
        
        .info {
            background: #e0f2fe;
            border: 1px solid #0284c7;
            color: #075985;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        
        /* Book table styles */
        .book-table-container {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        
        .search-bar {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }
        
        .search-input {
            flex: 1;
            padding: 10px;
            border: 1px solid #e5e7eb;
            border-radius: 5px;
            font-size: 16px;
        }
        
        .search-button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        
        .search-button:hover {
            background: #764ba2;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #f3f4f6;
        }
        
        tr:hover {
            background: #f9fafb;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
        }
        
        .page-button {
            padding: 8px 12px;
            border: 1px solid #e5e7eb;
            background: white;
            cursor: pointer;
            border-radius: 5px;
        }
        
        .page-button:hover {
            background: #f3f4f6;
        }
        
        .page-button.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .page-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .failed-books-section {
            background: #fef2f2;
            border: 1px solid #fecaca;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        
        .failed-book-item {
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            border: 1px solid #fecaca;
        }
        
        .error-message {
            color: #dc2626;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .retry-button {
            padding: 5px 10px;
            background: #f59e0b;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .retry-button:hover {
            background: #d97706;
        }
        
        .control-button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            font-weight: 600;
            transition: background 0.3s ease;
        }
        
        .pause-button {
            background: #f59e0b;
            color: white;
        }
        
        .pause-button:hover {
            background: #d97706;
        }
        
        .resume-button {
            background: #10b981;
            color: white;
        }
        
        .resume-button:hover {
            background: #059669;
        }
        
        .remaining-info {
            background: #fef3c7;
            border: 1px solid #fbbf24;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: bold;
        }
        
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab-button {
            padding: 10px 20px;
            background: #e5e7eb;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        
        .tab-button.active {
            background: #667eea;
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }
        
        .author-badge {
            display: inline-block;
            padding: 2px 8px;
            background: #e0e7ff;
            color: #4338ca;
            border-radius: 3px;
            font-size: 0.85em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔮 Spiritual Library Monitor</h1>
            <p>Enhanced monitoring with detailed book listings</p>
        </header>
        
        <div class="info">
            <strong>ℹ️ Note:</strong> This enhanced monitor shows detailed indexing progress, remaining books, and a complete table of all indexed books.
        </div>
        
        <div class="status-grid">
            <!-- Indexing Status -->
            <div class="card">
                <h2>Indexing Status</h2>
                <p>
                    <span id="status-indicator" class="status-indicator"></span>
                    <span id="status-text">Loading...</span>
                </p>
                <p class="timestamp" id="status-time"></p>
                <div id="progress-container" style="display:none;">
                    <div class="progress-bar">
                        <div id="progress-fill" class="progress-fill"></div>
                    </div>
                    <p id="progress-text"></p>
                    <div id="remaining-info" class="remaining-info"></div>
                </div>
                <div id="current-file" style="margin-top:10px;"></div>
                <div id="control-buttons" style="margin-top:15px;">
                    <button id="pause-btn" class="control-button pause-button" onclick="pauseIndexing()" style="display:none;">
                        ⏸️ Pause Indexing
                    </button>
                    <button id="resume-btn" class="control-button resume-button" onclick="resumeIndexing()" style="display:none;">
                        ▶️ Resume Indexing
                    </button>
                </div>
            </div>
            
            <!-- Library Statistics -->
            <div class="card">
                <h2>Library Statistics</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <div class="stat-value" id="total-books">0</div>
                        <div class="stat-label">Total Books</div>
                    </div>
                    <div>
                        <div class="stat-value" id="total-chunks">0</div>
                        <div class="stat-label">Text Chunks</div>
                    </div>
                    <div>
                        <div class="stat-value" id="pending-pdfs">0</div>
                        <div class="stat-label">Books Remaining</div>
                    </div>
                    <div>
                        <div class="stat-value" id="failed-pdfs">0</div>
                        <div class="stat-label">Failed Documents</div>
                    </div>
                </div>
            </div>
            
            <!-- Lock Status -->
            <div class="card">
                <h2>Lock Status</h2>
                <div id="lock-status">
                    <p>Checking lock status...</p>
                </div>
            </div>
        </div>
        
        <!-- Status Details -->
        <div class="card">
            <h2>Status Details</h2>
            <div id="recent-activity" class="file-list"></div>
        </div>
        
        <!-- Book Table Section -->
        <div class="book-table-container">
            <h2>📚 Indexed Books Library</h2>
            
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('indexed')">Indexed Books</button>
                <button class="tab-button" onclick="showTab('failed')">Failed Books</button>
            </div>
            
            <!-- Indexed Books Tab -->
            <div id="indexed-tab" class="tab-content active">
                <div class="search-bar">
                    <input type="text" id="search-input" class="search-input" placeholder="Search books by title, author, or category...">
                    <button class="search-button" onclick="searchBooks()">Search</button>
                    <button class="search-button" onclick="clearSearch()">Clear</button>
                </div>
                
                <div id="books-table-container">
                    <div class="loading">Loading books...</div>
                </div>
                
                <div id="pagination" class="pagination"></div>
            </div>
            
            <!-- Failed Books Tab -->
            <div id="failed-tab" class="tab-content">
                <div id="failed-books-container">
                    <div class="loading">Loading failed books...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentPage = 1;
        let totalPages = 1;
        let searchQuery = '';
        let allBooks = [];
        let failedBooks = {};
        
        function showTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Load data for the tab
            if (tabName === 'indexed') {
                loadBooks(1);
            } else if (tabName === 'failed') {
                loadFailedBooks();
            }
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update status indicator
                    const indicator = document.getElementById('status-indicator');
                    const statusText = document.getElementById('status-text');
                    const statusTime = document.getElementById('status-time');
                    
                    indicator.className = 'status-indicator status-' + data.status;
                    statusText.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                    statusTime.textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleString();
                    
                    // Update progress if indexing
                    const progressContainer = document.getElementById('progress-container');
                    if (data.status === 'indexing' && data.details) {
                        progressContainer.style.display = 'block';
                        const progress = data.details.progress || '0/0';
                        const [current, total] = progress.split('/').map(n => parseInt(n));
                        const percentage = total > 0 ? (current / total * 100) : 0;
                        const remaining = total - current;
                        
                        document.getElementById('progress-fill').style.width = percentage + '%';
                        document.getElementById('progress-text').textContent = 
                            `Progress: ${current}/${total} (${Math.round(percentage)}%)`;
                        
                        // Show remaining books in progress
                        document.getElementById('remaining-info').innerHTML = 
                            `📚 Processing ${current} of ${total} books (${remaining} remaining)`;
                        
                        if (data.details.current_file) {
                            document.getElementById('current-file').innerHTML = 
                                `<strong>Processing:</strong> ${data.details.current_file}`;
                        }
                    } else {
                        progressContainer.style.display = 'none';
                        document.getElementById('current-file').innerHTML = '';
                    }
                    
                    // Update activity details
                    const activityDiv = document.getElementById('recent-activity');
                    let details = [];
                    
                    if (data.details) {
                        if (data.details.last_run) {
                            details.push(`Last run: ${data.details.last_run}`);
                        }
                        if (data.details.indexed !== undefined) {
                            details.push(`Files indexed: ${data.details.indexed}`);
                        }
                        if (data.details.failed) {
                            details.push(`Files failed: ${data.details.failed}`);
                        }
                        if (data.details.current_file && data.status === 'indexing') {
                            details.push(`Currently processing: ${data.details.current_file}`);
                        }
                    }
                    
                    activityDiv.innerHTML = details.length > 0 
                        ? details.map(d => `<div class="file-item">${d}</div>`).join('')
                        : '<div class="file-item">No recent activity</div>';
                    
                    // Update pause/resume button visibility
                    updateControlButtons();
                })
                .catch(error => {
                    console.error('Error updating status:', error);
                });
        }
        
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-books').textContent = data.total_books;
                    document.getElementById('total-chunks').textContent = data.total_chunks.toLocaleString();
                    document.getElementById('pending-pdfs').textContent = data.pending_pdfs;
                    document.getElementById('failed-pdfs').textContent = data.failed_pdfs;
                })
                .catch(error => {
                    console.error('Error updating stats:', error);
                });
        }
        
        function updateLockStatus() {
            fetch('/api/lock-status')
                .then(response => response.json())
                .then(data => {
                    const lockDiv = document.getElementById('lock-status');
                    
                    if (data.exists) {
                        const isStale = data.stale;
                        const ageMinutes = Math.round(data.age_minutes || 0);
                        
                        lockDiv.innerHTML = `
                            <div class="lock-info ${isStale ? 'lock-stale' : ''}">
                                <p><strong>Lock Active</strong></p>
                                <p>PID: ${data.pid || 'Unknown'}</p>
                                <p>Age: ${ageMinutes} minutes</p>
                                ${isStale ? '<p>⚠️ This lock appears to be stale</p>' : ''}
                            </div>
                        `;
                    } else {
                        lockDiv.innerHTML = '<p>✅ No active lock</p>';
                    }
                })
                .catch(error => {
                    console.error('Error updating lock status:', error);
                });
        }
        
        function loadBooks(page = 1) {
            currentPage = page;
            const url = searchQuery 
                ? `/api/books?page=${page}&search=${encodeURIComponent(searchQuery)}`
                : `/api/books?page=${page}`;
                
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    allBooks = data.books;
                    totalPages = data.total_pages;
                    renderBooksTable(data.books);
                    renderPagination();
                })
                .catch(error => {
                    console.error('Error loading books:', error);
                    document.getElementById('books-table-container').innerHTML = 
                        '<div class="error-message">Error loading books</div>';
                });
        }
        
        function renderBooksTable(books) {
            if (books.length === 0) {
                document.getElementById('books-table-container').innerHTML = 
                    '<div class="file-item">No books found</div>';
                return;
            }
            
            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>Book Title</th>
                            <th>Author/Category</th>
                            <th>Pages</th>
                            <th>Chunks</th>
                            <th>Indexed Date</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            books.forEach(book => {
                const author = extractAuthor(book.path);
                const indexedDate = new Date(book.indexed_at).toLocaleDateString();
                
                html += `
                    <tr>
                        <td>${book.name}</td>
                        <td><span class="author-badge">${author}</span></td>
                        <td>${book.pages}</td>
                        <td>${book.chunks}</td>
                        <td>${indexedDate}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            document.getElementById('books-table-container').innerHTML = html;
        }
        
        function extractAuthor(path) {
            // Extract author/category from path
            const parts = path.split('/');
            if (parts.length > 1) {
                if (parts[0].includes("'s Books")) {
                    return parts[0].replace("'s Books", "");
                } else if (parts[0].includes("Books")) {
                    return parts[0].replace(" Books", "");
                }
            }
            return "General";
        }
        
        function renderPagination() {
            const paginationDiv = document.getElementById('pagination');
            let html = '';
            
            // Previous button
            html += `<button class="page-button" onclick="loadBooks(${currentPage - 1})" 
                     ${currentPage === 1 ? 'disabled' : ''}>Previous</button>`;
            
            // Page numbers
            let startPage = Math.max(1, currentPage - 2);
            let endPage = Math.min(totalPages, startPage + 4);
            
            if (endPage - startPage < 4) {
                startPage = Math.max(1, endPage - 4);
            }
            
            if (startPage > 1) {
                html += `<button class="page-button" onclick="loadBooks(1)">1</button>`;
                if (startPage > 2) html += '<span>...</span>';
            }
            
            for (let i = startPage; i <= endPage; i++) {
                html += `<button class="page-button ${i === currentPage ? 'active' : ''}" 
                         onclick="loadBooks(${i})">${i}</button>`;
            }
            
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) html += '<span>...</span>';
                html += `<button class="page-button" onclick="loadBooks(${totalPages})">${totalPages}</button>`;
            }
            
            // Next button
            html += `<button class="page-button" onclick="loadBooks(${currentPage + 1})" 
                     ${currentPage === totalPages ? 'disabled' : ''}>Next</button>`;
            
            // Page info
            html += `<span style="margin-left: 20px;">Page ${currentPage} of ${totalPages}</span>`;
            
            paginationDiv.innerHTML = html;
        }
        
        function searchBooks() {
            searchQuery = document.getElementById('search-input').value;
            loadBooks(1);
        }
        
        function clearSearch() {
            document.getElementById('search-input').value = '';
            searchQuery = '';
            loadBooks(1);
        }
        
        function loadFailedBooks() {
            fetch('/api/books/failed')
                .then(response => response.json())
                .then(data => {
                    failedBooks = data;
                    renderFailedBooks();
                })
                .catch(error => {
                    console.error('Error loading failed books:', error);
                });
        }
        
        function renderFailedBooks() {
            const container = document.getElementById('failed-books-container');
            
            if (Object.keys(failedBooks).length === 0) {
                container.innerHTML = '<div class="file-item">No failed books</div>';
                return;
            }
            
            let html = '<div class="failed-books-section">';
            
            for (const [bookName, details] of Object.entries(failedBooks)) {
                const failedDate = new Date(details.failed_at).toLocaleString();
                
                html += `
                    <div class="failed-book-item">
                        <strong>${bookName}</strong>
                        <div class="error-message">${details.error}</div>
                        <div class="timestamp">Failed at: ${failedDate} | Attempts: ${details.retry_count}</div>
                        <button class="retry-button" onclick="retryBook('${bookName}')">Retry</button>
                    </div>
                `;
            }
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        function retryBook(bookName) {
            if (confirm(`Retry indexing ${bookName}?`)) {
                fetch(`/api/retry/${encodeURIComponent(bookName)}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        loadFailedBooks();
                    })
                    .catch(error => {
                        alert('Error retrying book: ' + error);
                    });
            }
        }
        
        function updateControlButtons() {
            // Check pause status to determine which button to show
            fetch('/api/pause-status')
                .then(response => response.json())
                .then(data => {
                    const pauseBtn = document.getElementById('pause-btn');
                    const resumeBtn = document.getElementById('resume-btn');
                    
                    // Check current indexing status
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(statusData => {
                            if (statusData.status === 'indexing' || statusData.status === 'paused') {
                                // Show controls
                                if (data.paused) {
                                    pauseBtn.style.display = 'none';
                                    resumeBtn.style.display = 'inline-block';
                                } else {
                                    pauseBtn.style.display = 'inline-block';
                                    resumeBtn.style.display = 'none';
                                }
                            } else {
                                // Hide controls when not indexing
                                pauseBtn.style.display = 'none';
                                resumeBtn.style.display = 'none';
                            }
                        });
                })
                .catch(error => {
                    console.error('Error checking pause status:', error);
                });
        }
        
        function pauseIndexing() {
            fetch('/api/pause', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        updateControlButtons();
                        updateStatus();
                    } else {
                        alert('Error pausing indexing: ' + data.message);
                    }
                })
                .catch(error => {
                    alert('Error pausing indexing: ' + error);
                });
        }
        
        function resumeIndexing() {
            fetch('/api/resume', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success' || data.status === 'info') {
                        updateControlButtons();
                        updateStatus();
                    } else {
                        alert('Error resuming indexing: ' + data.message);
                    }
                })
                .catch(error => {
                    alert('Error resuming indexing: ' + error);
                });
        }
        
        // Initial load
        updateStatus();
        updateStats();
        updateLockStatus();
        loadBooks(1);
        
        // Auto-refresh
        setInterval(updateStatus, 2000);
        setInterval(updateStats, 5000);
        setInterval(updateLockStatus, 5000);
        
        // Refresh book table if indexing
        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'indexing') {
                        loadBooks(currentPage);
                    }
                });
        }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main monitoring page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    """Get current indexing status"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                return jsonify(json.load(f))
        except:
            pass
    return jsonify({"status": "idle", "timestamp": datetime.now().isoformat()})

@app.route('/api/stats')
def api_stats():
    """Get library statistics"""
    stats = {
        'total_books': 0,
        'total_chunks': 0,
        'failed_pdfs': 0,
        'pending_pdfs': 0
    }
    
    # Count indexed books
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r') as f:
                book_index = json.load(f)
                stats['total_books'] = len(book_index)
                stats['total_chunks'] = sum(entry.get('chunks', 0) for entry in book_index.values())
        except Exception as e:
            print(f"Error reading book index: {e}")
    
    # Count failed PDFs
    if os.path.exists(FAILED_PDFS_FILE):
        try:
            with open(FAILED_PDFS_FILE, 'r') as f:
                failed_pdfs = json.load(f)
                stats['failed_pdfs'] = len(failed_pdfs)
        except:
            pass
    
    # Count pending PDFs - use session data during active indexing for accuracy
    try:
        # Check for active indexing session with detailed progress
        session_remaining = None
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, 'r') as f:
                    status_data = json.load(f)
                    if (status_data.get('status') == 'indexing' and 
                        'details' in status_data and 
                        'progress' in status_data['details']):
                        
                        details = status_data['details']
                        progress_parts = details['progress'].split('/')
                        if len(progress_parts) == 2:
                            total_session = int(progress_parts[1])
                            success_session = details.get('success', 0)
                            failed_session = details.get('failed', 0)
                            # Calculate remaining: total - success - failed - currently_processing
                            session_remaining = max(0, total_session - success_session - failed_session - 1)
            except:
                pass
        
        if session_remaining is not None:
            # During active indexing, use real-time session progress
            stats['pending_pdfs'] = session_remaining
        else:
            # When idle, use file system calculation
            pdf_files = glob.glob(os.path.join(BOOKS_DIR, "**/*.pdf"), recursive=True)
            total_pdf_count = len(pdf_files)
            stats['pending_pdfs'] = max(0, total_pdf_count - stats['total_books'] - stats['failed_pdfs'])
            stats['total_pdfs'] = total_pdf_count
    except:
        pass
    
    return jsonify(stats)

@app.route('/api/lock-status')
def api_lock_status():
    """Get lock status information"""
    lock_info = {
        'exists': os.path.exists(LOCK_FILE),
        'stale': False,
        'pid': None,
        'age_minutes': 0
    }
    
    if lock_info['exists']:
        try:
            # Get file age
            mtime = os.path.getmtime(LOCK_FILE)
            lock_info['age_minutes'] = (datetime.now().timestamp() - mtime) / 60
            
            # Try to read PID
            with open(LOCK_FILE, 'r') as f:
                lines = f.readlines()
                if lines:
                    lock_info['pid'] = int(lines[0].strip())
                    
                    # Check if process is alive
                    try:
                        os.kill(lock_info['pid'], 0)
                    except ProcessLookupError:
                        lock_info['stale'] = True
                    except:
                        pass
            
            # Consider old locks as stale (2 minutes with periodic updates)
            if lock_info['age_minutes'] > 2:
                lock_info['stale'] = True
                
        except:
            pass
    
    return jsonify(lock_info)

@app.route('/api/books')
def api_books():
    """Get paginated list of indexed books"""
    page = int(request.args.get('page', 1))
    per_page = 50
    search = request.args.get('search', '').lower()
    
    books = []
    
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r') as f:
                book_index = json.load(f)
                
                for path, info in book_index.items():
                    book_name = os.path.basename(path)
                    
                    # Apply search filter
                    if search and search not in book_name.lower() and search not in path.lower():
                        continue
                    
                    books.append({
                        'name': book_name,
                        'path': path,
                        'pages': info.get('pages', 0),
                        'chunks': info.get('chunks', 0),
                        'indexed_at': info.get('indexed_at', ''),
                        'hash': info.get('hash', '')
                    })
        except:
            pass
    
    # Sort by name
    books.sort(key=lambda x: x['name'].lower())
    
    # Pagination
    total_books = len(books)
    total_pages = math.ceil(total_books / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_books = books[start:end]
    
    return jsonify({
        'books': paginated_books,
        'page': page,
        'per_page': per_page,
        'total_books': total_books,
        'total_pages': total_pages
    })

@app.route('/api/books/failed')
def api_failed_books():
    """Get detailed list of failed books"""
    failed_books = {}
    
    if os.path.exists(FAILED_PDFS_FILE):
        try:
            with open(FAILED_PDFS_FILE, 'r') as f:
                failed_books = json.load(f)
        except:
            pass
    
    return jsonify(failed_books)

@app.route('/api/retry/<book_name>', methods=['POST'])
def api_retry_book(book_name):
    """Retry indexing a failed book"""
    # This endpoint would need to be implemented with actual retry logic
    # For now, just remove from failed list
    
    if os.path.exists(FAILED_PDFS_FILE):
        try:
            with open(FAILED_PDFS_FILE, 'r') as f:
                failed_pdfs = json.load(f)
            
            if book_name in failed_pdfs:
                del failed_pdfs[book_name]
                
                with open(FAILED_PDFS_FILE, 'w') as f:
                    json.dump(failed_pdfs, f, indent=2)
                
                return jsonify({'success': True, 'message': f'Cleared {book_name} from failed list. Run indexing to retry.'})
            else:
                return jsonify({'success': False, 'message': 'Book not found in failed list'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    return jsonify({'success': False, 'message': 'Failed books file not found'})

@app.route('/api/pause', methods=['POST'])
def pause_indexing():
    """Pause the indexing process"""
    pause_file = "/tmp/spiritual_library_index.pause"
    try:
        with open(pause_file, 'w') as f:
            f.write(datetime.now().isoformat())
        return jsonify({
            "status": "success",
            "message": "Indexing paused"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/resume', methods=['POST'])
def resume_indexing():
    """Resume the indexing process"""
    pause_file = "/tmp/spiritual_library_index.pause"
    try:
        if os.path.exists(pause_file):
            os.remove(pause_file)
            return jsonify({
                "status": "success",
                "message": "Indexing resumed"
            })
        else:
            return jsonify({
                "status": "info",
                "message": "Indexing was not paused"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/pause-status')
def pause_status():
    """Check if indexing is paused"""
    pause_file = "/tmp/spiritual_library_index.pause"
    if os.path.exists(pause_file):
        try:
            with open(pause_file, 'r') as f:
                pause_time = f.read().strip()
            return jsonify({
                "paused": True,
                "pause_time": pause_time
            })
        except:
            return jsonify({
                "paused": True,
                "pause_time": "Unknown"
            })
    else:
        return jsonify({
            "paused": False
        })

if __name__ == '__main__':
    print("🔮 Starting Enhanced Spiritual Library Web Monitor")
    print("📌 Open http://localhost:8888 in your browser")
    print("   Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=8888, debug=False)