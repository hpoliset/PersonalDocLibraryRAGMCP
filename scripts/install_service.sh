#!/bin/bash
# Install the Spiritual Library Index Monitor as a LaunchAgent

echo "🔮 Installing Spiritual Library Index Monitor Service"
echo "==================================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only!"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLIST_NAME="com.spiritual-library.index-monitor"
PLIST_FILE="$PROJECT_ROOT/config/$PLIST_NAME.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_NAME.plist"

# Generate configs if they don't exist
if [ ! -f "$PLIST_FILE" ]; then
    echo "📌 Generating configuration files..."
    "${SCRIPT_DIR}/generate_configs.sh"
fi

# Check if already installed
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "⚠️  Service is already installed and running!"
    echo "   Use ./uninstall_service.sh to remove it first."
    exit 1
fi

# Check if plist exists
if [ ! -f "$PLIST_FILE" ]; then
    echo "❌ Plist file not found at: $PLIST_FILE"
    echo "   Please ensure the configuration file exists."
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist to LaunchAgents
echo "📌 Installing service configuration..."
cp "$PLIST_FILE" "$INSTALLED_PLIST"

# Load the service
echo "📌 Loading service..."
launchctl load "$INSTALLED_PLIST"

# Give it a moment to start
sleep 2

# Check if service is running
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "✅ Service installed and started successfully!"
    echo ""
    echo "Service Information:"
    echo "- Name: $PLIST_NAME"
    echo "- Config: $INSTALLED_PLIST"
    echo "- Logs: ~/AITools/logs/index_monitor_*.log"
    echo ""
    echo "To check status: ./service_status.sh"
    echo "To stop service: ./uninstall_service.sh"
    echo "To view logs: tail -f index_monitor_stdout.log"
else
    echo "❌ Service failed to start!"
    echo "   Check logs at: ~/AITools/logs/index_monitor_stderr.log"
    exit 1
fi