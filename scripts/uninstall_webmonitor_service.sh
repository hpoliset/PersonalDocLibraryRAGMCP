#!/bin/bash
# Uninstall the Spiritual Library Web Monitor LaunchAgent

echo "🔮 Uninstalling Spiritual Library Web Monitor Service"
echo "====================================================="
echo ""

PLIST_NAME="com.spiritual-library.webmonitor"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_NAME.plist"

# Check if service is installed
if ! launchctl list | grep -q "$PLIST_NAME"; then
    echo "ℹ️  Web Monitor service is not currently running."
else
    echo "📌 Stopping service..."
    launchctl unload "$INSTALLED_PLIST" 2>/dev/null
    
    # Give it a moment to stop
    sleep 2
    
    # Force kill if still running
    PID=$(pgrep -f "python.*monitor_web_enhanced.py")
    if [ ! -z "$PID" ]; then
        echo "⚠️  Force stopping process (PID: $PID)..."
        kill -TERM $PID 2>/dev/null
        sleep 1
        kill -9 $PID 2>/dev/null
    fi
fi

# Remove plist file
if [ -f "$INSTALLED_PLIST" ]; then
    echo "📌 Removing service configuration..."
    rm -f "$INSTALLED_PLIST"
fi

# Verify removal
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "❌ Failed to uninstall service completely!"
    echo "   You may need to restart your system."
    exit 1
else
    echo "✅ Web Monitor service uninstalled successfully!"
    echo ""
    echo "Note: Log files have been preserved at:"
    echo "- webmonitor_stdout.log"
    echo "- webmonitor_stderr.log"
    echo ""
    echo "🌐 Web interface is no longer available at http://localhost:8888"
fi