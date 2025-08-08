#!/bin/bash
# Uninstall the Personal Document Library Index Monitor LaunchAgent

echo "🔮 Uninstalling Personal Document Library Index Monitor Service"
echo "======================================================="
echo ""

PLIST_NAME="com.personal-library.index-monitor"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_NAME.plist"

# Check if service is installed
if ! launchctl list | grep -q "$PLIST_NAME"; then
    echo "ℹ️  Service is not currently running."
else
    echo "📌 Stopping service..."
    launchctl unload "$INSTALLED_PLIST" 2>/dev/null
    
    # Give it a moment to stop
    sleep 2
    
    # Force kill if still running (try both patterns)
    PID1=$(pgrep -f "python.*index_monitor.py.*--service" 2>/dev/null)
    PID2=$(pgrep -f "python.*index_monitor.py" 2>/dev/null | head -1)
    
    for PID in $PID1 $PID2; do
        if [ ! -z "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  Force stopping process (PID: $PID)..."
            kill -TERM $PID 2>/dev/null
            sleep 1
            kill -9 $PID 2>/dev/null
        fi
    done
fi

# Remove plist file
if [ -f "$INSTALLED_PLIST" ]; then
    echo "📌 Removing service configuration..."
    rm -f "$INSTALLED_PLIST"
fi

# Clean up lock file if exists
if [ -f "/tmp/spiritual_library_index.lock" ]; then
    echo "📌 Cleaning up lock file..."
    rm -f /tmp/spiritual_library_index.lock
fi

# Verify removal
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "❌ Failed to uninstall service completely!"
    echo "   You may need to restart your system."
    exit 1
else
    echo "✅ Service uninstalled successfully!"
    echo ""
    echo "Note: Log files have been preserved at:"
    echo "- index_monitor_stdout.log"
    echo "- index_monitor_stderr.log"
fi