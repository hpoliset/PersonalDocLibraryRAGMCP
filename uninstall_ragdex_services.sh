#!/bin/bash

# Uninstall ragdex services

echo "🔧 Ragdex Service Uninstaller"
echo "============================"
echo ""

# Load saved configuration if it exists
CONFIG_FILE="$HOME/.ragdex/service_config"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    echo "📋 Loaded configuration from $CONFIG_FILE"
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Service plists
INDEX_PLIST="$HOME/Library/LaunchAgents/com.ragdex.indexer.plist"
WEB_PLIST="$HOME/Library/LaunchAgents/com.ragdex.webmonitor.plist"

# Unload services
echo "Stopping services..."

if launchctl list | grep -q com.ragdex.indexer; then
    launchctl unload "$INDEX_PLIST" 2>/dev/null
    echo -e "${GREEN}✓${NC} Indexer service stopped"
else
    echo "ℹ️  Indexer service not running"
fi

if launchctl list | grep -q com.ragdex.webmonitor; then
    launchctl unload "$WEB_PLIST" 2>/dev/null
    echo -e "${GREEN}✓${NC} Web monitor service stopped"
else
    echo "ℹ️  Web monitor service not running"
fi

# Remove plist files
echo ""
echo "Removing service configurations..."

if [ -f "$INDEX_PLIST" ]; then
    rm "$INDEX_PLIST"
    echo -e "${GREEN}✓${NC} Removed indexer configuration"
fi

if [ -f "$WEB_PLIST" ]; then
    rm "$WEB_PLIST"
    echo -e "${GREEN}✓${NC} Removed web monitor configuration"
fi

echo ""
echo "✅ Services uninstalled"
echo ""
echo "Note: Log files preserved at ~/DocumentIndexerMCP/logs/"
echo "Note: Ragdex package still installed at ~/ragdex_env/"
echo ""
echo "To completely remove ragdex:"
echo "   rm -rf ~/ragdex_env"
echo "   rm -rf ~/DocumentIndexerMCP/logs/ragdex_*.log"