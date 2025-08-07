#!/bin/bash
# Check status of the Personal Document Library Index Monitor service

echo "🔮 Personal Document Library Index Monitor - Service Status"
echo "==================================================="
echo ""

PLIST_NAME="com.spiritual-library.index-monitor"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if service is loaded
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "✅ Service is installed and loaded"
    
    # Get service details
    SERVICE_INFO=$(launchctl list | grep "$PLIST_NAME")
    PID=$(echo "$SERVICE_INFO" | awk '{print $1}')
    STATUS=$(echo "$SERVICE_INFO" | awk '{print $2}')
    
    echo ""
    echo "Service Details:"
    echo "- PID: $PID"
    echo "- Exit Status: $STATUS"
    
    if [ "$PID" != "-" ]; then
        echo "- Status: RUNNING"
        
        # Get process info
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "- Memory: $(ps -p $PID -o rss= | awk '{print int($1/1024) "MB"}')"
            echo "- CPU: $(ps -p $PID -o %cpu= | awk '{print $1"%"}')"
        fi
    else
        echo "- Status: NOT RUNNING"
        if [ "$STATUS" != "0" ]; then
            echo "- ⚠️  Last exit was abnormal (code: $STATUS)"
        fi
    fi
else
    echo "❌ Service is not installed"
    echo "   Run ./install_service.sh to install"
fi

# Check lock status
echo ""
echo "Lock Status:"
if [ -f "/tmp/spiritual_library_index.lock" ]; then
    echo "- Lock file exists"
    if [ -r "/tmp/spiritual_library_index.lock" ]; then
        LOCK_INFO=$(cat /tmp/spiritual_library_index.lock 2>/dev/null)
        LOCK_PID=$(echo "$LOCK_INFO" | head -1)
        LOCK_TIME=$(echo "$LOCK_INFO" | tail -1)
        echo "- Held by PID: $LOCK_PID"
        echo "- Since: $LOCK_TIME"
        
        # Check if process is alive
        if ps -p "$LOCK_PID" > /dev/null 2>&1; then
            echo "- Process: ALIVE ✅"
        else
            echo "- Process: DEAD ❌ (stale lock)"
        fi
    fi
else
    echo "- No active lock"
fi

# Check index status
echo ""
echo "Index Status:"
if [ -f "$SCRIPT_DIR/../chroma_db/index_status.json" ]; then
    # Extract key fields using python
    $SCRIPT_DIR/../venv_mcp/bin/python -c "
import json
with open('$SCRIPT_DIR/../chroma_db/index_status.json', 'r') as f:
    data = json.load(f)
    print(f\"- Status: {data.get('status', 'unknown').upper()}\")
    print(f\"- Last Update: {data.get('timestamp', 'unknown')}\")
    if 'details' in data:
        details = data['details']
        if 'current_file' in details:
            print(f\"- Current File: {details['current_file']}\")
        if 'last_run' in details:
            print(f\"- Last Run: {details['last_run']}\")
        if 'indexed' in details:
            print(f\"- Files Indexed: {details['indexed']}\")
        if 'failed' in details and details['failed'] > 0:
            print(f\"- Files Failed: {details['failed']} ⚠️\")
" 2>/dev/null || echo "- Unable to read status file"
else
    echo "- No status file found"
fi

# Check for new PDFs
echo ""
echo "Checking for new PDFs..."
$SCRIPT_DIR/../venv_mcp/bin/python -c "
import sys
sys.path.append('$SCRIPT_DIR/..')
try:
    from src.core.shared_rag import SharedRAG
    rag = SharedRAG()
    new_pdfs = rag.find_new_or_modified_pdfs()
    if new_pdfs:
        print(f'- {len(new_pdfs)} PDFs need indexing:')
        for _, rel_path in new_pdfs[:5]:
            print(f'  • {rel_path}')
        if len(new_pdfs) > 5:
            print(f'  • ... and {len(new_pdfs) - 5} more')
    else:
        print('- All PDFs are up to date ✅')
except Exception as e:
    print(f'- Error checking PDFs: {e}')
" 2>/dev/null

# Check log files
echo ""
echo "Recent Log Activity:"
if [ -f "$SCRIPT_DIR/../logs/index_monitor_stdout.log" ]; then
    echo "- stdout: $(tail -1 $SCRIPT_DIR/../logs/index_monitor_stdout.log 2>/dev/null || echo 'empty')"
fi
if [ -f "$SCRIPT_DIR/../logs/index_monitor_stderr.log" ]; then
    LAST_ERROR=$(tail -1 $SCRIPT_DIR/../logs/index_monitor_stderr.log 2>/dev/null)
    if [ ! -z "$LAST_ERROR" ]; then
        echo "- stderr: $LAST_ERROR ⚠️"
    fi
fi

echo ""
echo "Commands:"
echo "- View logs: tail -f logs/index_monitor_stdout.log"
echo "- Stop service: ./uninstall_service.sh"
echo "- Restart service: ./uninstall_service.sh && ./install_service.sh"