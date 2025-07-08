#!/bin/bash
# Stop the background index monitor

echo "🔮 Stopping Index Monitor"
echo "========================"
echo ""

# Find and stop monitor process
PID=$(pgrep -f "python.*index_monitor.py")

if [ -z "$PID" ]; then
    echo "ℹ️  Index monitor is not running."
else
    echo "📌 Stopping monitor process (PID: $PID)..."
    kill -TERM $PID
    
    # Wait for graceful shutdown
    sleep 2
    
    # Check if still running
    if pgrep -f "python.*index_monitor.py" > /dev/null; then
        echo "⚠️  Monitor didn't stop gracefully, forcing..."
        kill -9 $PID
    fi
    
    echo "✅ Monitor stopped successfully."
fi

# Clean up lock file if exists
if [ -f "/tmp/spiritual_library_index.lock" ]; then
    rm -f /tmp/spiritual_library_index.lock
    echo "✅ Cleaned up lock file."
fi