#!/bin/bash

# Check status of ragdex services and installation

echo "📊 Ragdex Status Check"
echo "====================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check installation
echo "${BLUE}📦 Installation:${NC}"
echo ""

# Check PyPI version
PYPI_VERSION=$(curl -s https://pypi.org/pypi/ragdex/json | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
echo "   Latest PyPI version: $PYPI_VERSION"

# Check local installation
if [ -d "$HOME/ragdex_env" ]; then
    INSTALLED_VERSION=$($HOME/ragdex_env/bin/python -c "import pkg_resources; print(pkg_resources.get_distribution('ragdex').version)" 2>/dev/null || echo "unknown")
    echo -e "   Local version: $INSTALLED_VERSION ${GREEN}✓${NC}"

    if [ "$INSTALLED_VERSION" != "$PYPI_VERSION" ] && [ "$INSTALLED_VERSION" != "unknown" ]; then
        echo -e "   ${YELLOW}⚠️  Update available! Run: uv pip install --upgrade ragdex${NC}"
    fi
else
    echo -e "   ${RED}✗ Not installed${NC}"
    echo "   To install: uv venv ~/ragdex_env && cd ~/ragdex_env && uv pip install ragdex"
fi

echo ""
echo "${BLUE}🔧 Services:${NC}"
echo ""

# Check indexer service
if launchctl list | grep -q com.ragdex.indexer; then
    PID=$(launchctl list | grep com.ragdex.indexer | awk '{print $1}')
    if [ "$PID" != "-" ]; then
        echo -e "   Indexer: ${GREEN}● Running${NC} (PID: $PID)"
    else
        echo -e "   Indexer: ${YELLOW}○ Loaded but not running${NC}"
    fi
else
    echo -e "   Indexer: ${RED}○ Not installed${NC}"
fi

# Check web monitor service
if launchctl list | grep -q com.ragdex.webmonitor; then
    PID=$(launchctl list | grep com.ragdex.webmonitor | awk '{print $1}')
    if [ "$PID" != "-" ]; then
        echo -e "   Web Monitor: ${GREEN}● Running${NC} (PID: $PID)"

        # Check if web interface is accessible
        if curl -s http://localhost:8888 >/dev/null 2>&1; then
            echo -e "   Web Interface: ${GREEN}✓ Accessible${NC} at http://localhost:8888"
        else
            echo -e "   Web Interface: ${YELLOW}⚠️  Not responding${NC}"
        fi
    else
        echo -e "   Web Monitor: ${YELLOW}○ Loaded but not running${NC}"
    fi
else
    echo -e "   Web Monitor: ${RED}○ Not installed${NC}"
fi

echo ""
echo "${BLUE}📂 Data Locations:${NC}"
echo ""

# Check directories
DOCS_DIR="$HOME/SpiritualLibrary"
DB_DIR="$HOME/DocumentIndexerMCP/chroma_db"
LOGS_DIR="$HOME/DocumentIndexerMCP/logs"

for dir_info in "$DOCS_DIR:Documents" "$DB_DIR:Database" "$LOGS_DIR:Logs"; do
    IFS=':' read -r DIR_PATH DIR_NAME <<< "$dir_info"
    if [ -d "$DIR_PATH" ]; then
        COUNT=$(ls -1 "$DIR_PATH" 2>/dev/null | wc -l | tr -d ' ')
        echo -e "   $DIR_NAME: ${GREEN}✓${NC} $DIR_PATH ($COUNT items)"
    else
        echo -e "   $DIR_NAME: ${YELLOW}○${NC} $DIR_PATH (not created yet)"
    fi
done

# Check recent logs
echo ""
echo "${BLUE}📝 Recent Log Activity:${NC}"
echo ""

if [ -d "$LOGS_DIR" ]; then
    for log in ragdex_indexer_stderr.log ragdex_web_stderr.log; do
        if [ -f "$LOGS_DIR/$log" ]; then
            LAST_LINE=$(tail -1 "$LOGS_DIR/$log" 2>/dev/null | cut -c1-60)
            if [ -n "$LAST_LINE" ]; then
                echo "   $log: $LAST_LINE..."
            fi
        fi
    done
fi

# Check Claude Desktop integration
echo ""
echo "${BLUE}🤖 Claude Desktop Integration:${NC}"
echo ""

CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -f "$CONFIG_FILE" ]; then
    if grep -q "ragdex" "$CONFIG_FILE"; then
        echo -e "   ${GREEN}✓${NC} Ragdex configured in Claude Desktop"
    else
        echo -e "   ${YELLOW}○${NC} Not configured in Claude Desktop"
        echo "   Update config to use: $HOME/ragdex_env/bin/ragdex-mcp"
    fi
else
    echo -e "   ${RED}✗${NC} Claude Desktop config not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Quick Actions:"
echo "  Install services: ./install_ragdex_services.sh"
echo "  Uninstall services: ./uninstall_ragdex_services.sh"
echo "  View logs: tail -f ~/DocumentIndexerMCP/logs/ragdex_*.log"
echo "  Update ragdex: cd ~/ragdex_env && uv pip install --upgrade ragdex"