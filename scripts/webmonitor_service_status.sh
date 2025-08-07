#!/bin/bash
# Check status of the Personal Document Library Web Monitor service

echo "🔮 Personal Document Library Web Monitor - Service Status"
echo "================================================="
echo ""

PLIST_NAME="com.spiritual-library.webmonitor"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if service is loaded
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "✅ Web Monitor service is installed and loaded"
    
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
        echo "- Web Interface: http://localhost:8888"
        
        # Get process info
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "- Memory: $(ps -p $PID -o rss= | awk '{print int($1/1024) "MB"}')"
            echo "- CPU: $(ps -p $PID -o %cpu= | awk '{print $1"%"}')"
        fi
        
        # Test web interface
        echo ""
        echo "Web Interface Test:"
        if curl -s -m 5 http://localhost:8888 >/dev/null 2>&1; then
            echo "- ✅ Web interface is responding at http://localhost:8888"
        else
            echo "- ❌ Web interface not responding (may still be starting)"
        fi
    else
        echo "- Status: NOT RUNNING"
        if [ "$STATUS" != "0" ]; then
            echo "- ⚠️  Last exit was abnormal (code: $STATUS)"
        fi
    fi
else
    echo "❌ Web Monitor service is not installed"
    echo "   Run ./install_webmonitor_service.sh to install"
fi

# Check port 8888
echo ""
echo "Port Status:"
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PROCESS=$(lsof -Pi :8888 -sTCP:LISTEN | tail -n +2 | awk '{print $1, $2}')
    echo "- Port 8888: OCCUPIED by $PROCESS"
else
    echo "- Port 8888: Available"
fi

# Check recent log activity
echo ""
echo "Recent Log Activity:"
if [ -f "$SCRIPT_DIR/../logs/webmonitor_stdout.log" ]; then
    LAST_OUTPUT=$(tail -1 "$SCRIPT_DIR/../logs/webmonitor_stdout.log" 2>/dev/null)
    if [ ! -z "$LAST_OUTPUT" ]; then
        echo "- stdout: $LAST_OUTPUT"
    else
        echo "- stdout: (empty)"
    fi
fi
if [ -f "$SCRIPT_DIR/../logs/webmonitor_stderr.log" ]; then
    LAST_ERROR=$(tail -1 "$SCRIPT_DIR/../logs/webmonitor_stderr.log" 2>/dev/null)
    if [ ! -z "$LAST_ERROR" ]; then
        echo "- stderr: $LAST_ERROR ⚠️"
    fi
fi

echo ""
echo "Commands:"
echo "- Open web interface: open http://localhost:8888"
echo "- View logs: tail -f logs/webmonitor_stdout.log"
echo "- Stop service: ./uninstall_webmonitor_service.sh"
echo "- Restart service: ./uninstall_webmonitor_service.sh && ./install_webmonitor_service.sh"