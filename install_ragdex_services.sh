#!/bin/bash

# Install ragdex services from PyPI version
# This script installs both the indexer and web monitor as LaunchAgent services

set -e

echo "🚀 Ragdex Service Installer (PyPI Version)"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if ragdex is installed
RAGDEX_ENV="$HOME/ragdex_env"

if [ ! -d "$RAGDEX_ENV" ]; then
    echo "📦 Installing ragdex from PyPI..."
    cd ~
    uv venv ragdex_env
    cd ragdex_env
    uv pip install ragdex
    echo -e "${GREEN}✓${NC} Ragdex installed successfully"
else
    echo -e "${GREEN}✓${NC} Found ragdex installation at $RAGDEX_ENV"

    # Check for updates
    echo "Checking for updates..."
    cd "$RAGDEX_ENV"
    uv pip install --upgrade ragdex
fi

# Verify commands exist
echo ""
echo "Verifying installation..."
for cmd in ragdex ragdex-mcp ragdex-index ragdex-web; do
    if [ -f "$RAGDEX_ENV/bin/$cmd" ]; then
        echo -e "${GREEN}✓${NC} $cmd found"
    else
        echo -e "${RED}✗${NC} $cmd not found"
        exit 1
    fi
done

# Create service plists
echo ""
echo "📝 Creating service configurations..."

# Service 1: Background Indexer
INDEX_PLIST="$HOME/Library/LaunchAgents/com.ragdex.indexer.plist"
cat > "$INDEX_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ragdex.indexer</string>

    <key>ProgramArguments</key>
    <array>
        <string>$RAGDEX_ENV/bin/ragdex-index</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PERSONAL_LIBRARY_DOC_PATH</key>
        <string>$HOME/SpiritualLibrary</string>
        <key>PERSONAL_LIBRARY_DB_PATH</key>
        <string>$HOME/DocumentIndexerMCP/chroma_db</string>
        <key>PERSONAL_LIBRARY_LOGS_PATH</key>
        <string>$HOME/DocumentIndexerMCP/logs</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>CHROMA_TELEMETRY</key>
        <string>false</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$HOME/DocumentIndexerMCP/logs/ragdex_indexer_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$HOME/DocumentIndexerMCP/logs/ragdex_indexer_stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>ProcessType</key>
    <string>Background</string>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
EOF

echo -e "${GREEN}✓${NC} Created indexer service configuration"

# Service 2: Web Monitor
WEB_PLIST="$HOME/Library/LaunchAgents/com.ragdex.webmonitor.plist"
cat > "$WEB_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ragdex.webmonitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>$RAGDEX_ENV/bin/ragdex-web</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PERSONAL_LIBRARY_DOC_PATH</key>
        <string>$HOME/SpiritualLibrary</string>
        <key>PERSONAL_LIBRARY_DB_PATH</key>
        <string>$HOME/DocumentIndexerMCP/chroma_db</string>
        <key>PERSONAL_LIBRARY_LOGS_PATH</key>
        <string>$HOME/DocumentIndexerMCP/logs</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>CHROMA_TELEMETRY</key>
        <string>false</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$HOME/DocumentIndexerMCP/logs/ragdex_web_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$HOME/DocumentIndexerMCP/logs/ragdex_web_stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

echo -e "${GREEN}✓${NC} Created web monitor service configuration"

# Create log directory if needed
mkdir -p "$HOME/DocumentIndexerMCP/logs"

# Load services
echo ""
echo "🔧 Installing services..."

# Unload if already loaded
launchctl unload "$INDEX_PLIST" 2>/dev/null || true
launchctl unload "$WEB_PLIST" 2>/dev/null || true

# Load services
launchctl load "$INDEX_PLIST"
echo -e "${GREEN}✓${NC} Indexer service installed"

launchctl load "$WEB_PLIST"
echo -e "${GREEN}✓${NC} Web monitor service installed"

# Check status
echo ""
echo "📊 Service Status:"
echo ""

if launchctl list | grep -q com.ragdex.indexer; then
    echo -e "${GREEN}✓${NC} Indexer service is running"
else
    echo -e "${RED}✗${NC} Indexer service failed to start"
fi

if launchctl list | grep -q com.ragdex.webmonitor; then
    echo -e "${GREEN}✓${NC} Web monitor service is running"
    echo ""
    echo "🌐 Web interface available at: ${YELLOW}http://localhost:8888${NC}"
else
    echo -e "${RED}✗${NC} Web monitor service failed to start"
fi

echo ""
echo "📝 Log files:"
echo "   Indexer: ~/DocumentIndexerMCP/logs/ragdex_indexer_*.log"
echo "   Web: ~/DocumentIndexerMCP/logs/ragdex_web_*.log"
echo ""
echo "🎯 Service Management:"
echo "   Status: launchctl list | grep ragdex"
echo "   Stop: launchctl unload ~/Library/LaunchAgents/com.ragdex.*.plist"
echo "   Start: launchctl load ~/Library/LaunchAgents/com.ragdex.*.plist"
echo "   Logs: tail -f ~/DocumentIndexerMCP/logs/ragdex_*.log"
echo ""
echo "✅ Ragdex services installed successfully!"