#!/bin/bash
# Check the status of Personal Document Library indexing

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PAUSE_FILE="/tmp/spiritual_library_index.pause"
LOCK_FILE="/tmp/spiritual_library_index.lock"
STATUS_FILE="$PROJECT_ROOT/chroma_db/index_status.json"
STATS_URL="http://localhost:8888/api/stats"

echo "📊 Personal Document Library Indexing Status"
echo "===================================="
echo ""

# Check if paused
if [ -f "$PAUSE_FILE" ]; then
    PAUSE_TIME=$(cat "$PAUSE_FILE" 2>/dev/null || echo "Unknown")
    echo "⏸️  Status: PAUSED"
    echo "   Paused since: $PAUSE_TIME"
else
    echo "▶️  Status: RUNNING"
fi
echo ""

# Check lock status
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(head -1 "$LOCK_FILE" 2>/dev/null || echo "Unknown")
    LOCK_TIME=$(tail -1 "$LOCK_FILE" 2>/dev/null || echo "Unknown")
    
    # Check if process is alive
    if ps -p "$LOCK_PID" > /dev/null 2>&1; then
        echo "🔒 Lock Status: Active (PID: $LOCK_PID)"
    else
        echo "⚠️  Lock Status: Stale lock detected (dead PID: $LOCK_PID)"
    fi
    echo "   Lock created: $LOCK_TIME"
else
    echo "🔓 Lock Status: No lock file"
fi
echo ""

# Check current indexing status
if [ -f "$STATUS_FILE" ]; then
    echo "📋 Current Activity:"
    # Use python to pretty print the JSON
    if command -v python3 &> /dev/null; then
        python3 -c "
import json
with open('$STATUS_FILE', 'r') as f:
    data = json.load(f)
    print(f\"   Status: {data.get('status', 'unknown')}\" )
    print(f\"   Last Update: {data.get('timestamp', 'unknown')}\")
    if 'details' in data and data['details']:
        if 'current_file' in data['details']:
            print(f\"   Current File: {data['details']['current_file']}\")
        if 'progress' in data['details']:
            print(f\"   Progress: {data['details']['progress']}\")
"
    else
        cat "$STATUS_FILE"
    fi
else
    echo "❌ No status file found"
fi
echo ""

# Check library statistics from web monitor
if curl -s "$STATS_URL" > /dev/null 2>&1; then
    echo "📚 Library Statistics:"
    curl -s "$STATS_URL" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"   Total Books: {data.get('total_books', 0)}\")
print(f\"   Total Chunks: {data.get('total_chunks', 0)}\")
print(f\"   Pending PDFs: {data.get('pending_pdfs', 0)}\")
print(f\"   Failed PDFs: {data.get('failed_pdfs', 0)}\")
" 2>/dev/null || echo "   Error parsing statistics"
else
    echo "⚠️  Web monitor not running (start with ./scripts/start_web_monitor.sh)"
fi
echo ""

# Show control options
echo "🎮 Control Options:"
if [ -f "$PAUSE_FILE" ]; then
    echo "   Resume: ./scripts/resume_indexing.sh"
else
    echo "   Pause: ./scripts/pause_indexing.sh"
fi
echo "   Web Monitor: http://localhost:8888"
echo ""