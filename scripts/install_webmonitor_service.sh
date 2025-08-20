#!/bin/bash
# Install the Personal Document Library Web Monitor as a LaunchAgent

echo "🔮 Installing Personal Document Library Web Monitor Service"
echo "================================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only!"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PLIST_NAME="com.personal-library.webmonitor"
PLIST_FILE="$SCRIPT_DIR/../config/$PLIST_NAME.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_NAME.plist"

# Check if already installed
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "⚠️  Web Monitor service is already installed and running!"
    echo "   Use ./uninstall_webmonitor_service.sh to remove it first."
    exit 1
fi

# Check if plist exists
if [ ! -f "$PLIST_FILE" ]; then
    echo "❌ Plist file not found at: $PLIST_FILE"
    echo "   Please ensure the configuration file exists."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv_mcp" ]; then
    echo "❌ Virtual environment not found at $PROJECT_ROOT/venv_mcp!"
    echo "   Please run ./serviceInstall.sh first."
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/../logs"

# Copy plist to LaunchAgents
echo "📌 Installing service configuration..."
cp "$PLIST_FILE" "$INSTALLED_PLIST"

# Load the service
echo "📌 Loading service..."
launchctl load "$INSTALLED_PLIST"

# Give it a moment to start
sleep 3

# Check if service is running
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "✅ Web Monitor service installed and started successfully!"
    echo ""
    echo "Service Information:"
    echo "- Name: $PLIST_NAME"
    echo "- Config: $INSTALLED_PLIST"
    echo "- Web Interface: http://localhost:8888"
    echo "- Logs: ~/AITools/logs/webmonitor_*.log"
    echo ""
    echo "To check status: ./webmonitor_service_status.sh"
    echo "To stop service: ./uninstall_webmonitor_service.sh"
    echo "To view logs: tail -f logs/webmonitor_stdout.log"
    echo ""
    echo "🌐 Web Monitor will be available at: http://localhost:8888"
else
    echo "❌ Service failed to start!"
    echo "   Check logs at: ~/AITools/logs/webmonitor_stderr.log"
    exit 1
fi