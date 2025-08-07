#!/bin/bash

# Stop Web Monitor Script for Personal Document Library MCP Server

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔮 Stopping Personal Document Library Web Monitor"
echo "========================================="
echo ""

# Find and kill the process
if pgrep -f monitor_web_enhanced > /dev/null; then
    echo "📌 Stopping web monitor..."
    pkill -f monitor_web_enhanced
    
    # Wait for process to stop
    sleep 1
    
    if pgrep -f monitor_web_enhanced > /dev/null; then
        echo -e "${YELLOW}⚠️  Process didn't stop gracefully, forcing...${NC}"
        pkill -9 -f monitor_web_enhanced
    fi
    
    echo -e "${GREEN}✅ Web monitor stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Web monitor is not running${NC}"
fi