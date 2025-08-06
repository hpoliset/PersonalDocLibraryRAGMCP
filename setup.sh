#!/bin/bash

# Comprehensive Setup Script for Spiritual Library MCP Server
# Can be run both interactively and non-interactively

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🔮 Spiritual Library MCP Server - Setup 🔮            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Parse command line arguments
BOOKS_PATH=""
DB_PATH=""
INTERACTIVE=true
INSTALL_SERVICE=false
START_WEB_MONITOR=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --books-path)
            BOOKS_PATH="$2"
            shift 2
            ;;
        --db-path)
            DB_PATH="$2"
            shift 2
            ;;
        --non-interactive)
            INTERACTIVE=false
            shift
            ;;
        --install-service)
            INSTALL_SERVICE=true
            shift
            ;;
        --start-web-monitor)
            START_WEB_MONITOR=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --books-path PATH        Path to books directory"
            echo "  --db-path PATH          Path to database directory"
            echo "  --non-interactive       Run without prompts"
            echo "  --install-service       Install background service (macOS)"
            echo "  --start-web-monitor     Start web monitoring dashboard"
            echo "  --help                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  # Interactive setup"
            echo "  ./setup.sh"
            echo ""
            echo "  # Non-interactive with custom paths"
            echo "  ./setup.sh --books-path /Users/me/Books --non-interactive"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Step 1: Check Python
echo -e "${BLUE}📌 Checking Python installation...${NC}"
python_cmd=""
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "  ${GREEN}✓${NC} Python 3 found: $python_version"
    python_cmd="python3"
elif command -v python &> /dev/null; then
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    if [[ "$python_version" == 3.* ]]; then
        echo -e "  ${GREEN}✓${NC} Python 3 found: $python_version"
        python_cmd="python"
    fi
fi

if [ -z "$python_cmd" ]; then
    echo -e "  ${RED}✗${NC} Python 3.8+ is required but not found"
    echo "  Please install Python 3 and try again"
    exit 1
fi

# Step 2: Create/verify virtual environment
echo ""
echo -e "${BLUE}📌 Setting up virtual environment...${NC}"

venv_path="${PROJECT_ROOT}/venv_mcp"
if [ ! -d "$venv_path" ]; then
    echo "  Creating virtual environment..."
    $python_cmd -m venv "$venv_path"
    echo -e "  ${GREEN}✓${NC} Virtual environment created"
else
    echo -e "  ${GREEN}✓${NC} Virtual environment exists"
fi

# Fix Python symlinks if broken
if [ -L "$venv_path/bin/python" ] && [ ! -e "$venv_path/bin/python" ]; then
    echo "  Fixing Python symlinks..."
    cd "$venv_path/bin"
    rm -f python
    for pyver in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
        if [ -e "$pyver" ]; then
            ln -s "$pyver" python
            break
        fi
    done
    cd "$PROJECT_ROOT"
fi

# Step 3: Install dependencies
echo ""
echo -e "${BLUE}📌 Installing dependencies...${NC}"

# Activate virtual environment
source "$venv_path/bin/activate"

# Upgrade pip first
echo "  Upgrading pip..."
"$venv_path/bin/python" -m pip install --upgrade pip setuptools wheel --quiet

# Install core dependencies
echo "  Installing core dependencies..."
"$venv_path/bin/python" -m pip install --no-cache-dir --quiet \
    langchain==0.1.0 \
    langchain-community==0.0.10 \
    chromadb==0.4.22 \
    sentence-transformers \
    pypdf2==3.0.1 \
    pypandoc==1.12

# Install document processing dependencies
echo "  Installing document processing libraries..."
"$venv_path/bin/python" -m pip install --no-cache-dir --quiet \
    unstructured \
    python-docx \
    pypdf \
    openpyxl \
    pdfminer.six \
    python-dotenv \
    psutil \
    flask \
    'numpy<2.0'

echo -e "  ${GREEN}✓${NC} Dependencies installed"

# Step 4: Configure paths
echo ""
echo -e "${BLUE}📌 Configuring paths...${NC}"

# Set default paths if not provided
if [ -z "$BOOKS_PATH" ]; then
    # Check common locations
    if [ -d "/Users/${USER}/SpiritualLibrary" ]; then
        BOOKS_PATH="/Users/${USER}/SpiritualLibrary"
    elif [ -d "${HOME}/Documents/SpiritualLibrary" ]; then
        BOOKS_PATH="${HOME}/Documents/SpiritualLibrary"
    else
        BOOKS_PATH="${PROJECT_ROOT}/books"
    fi
fi

if [ -z "$DB_PATH" ]; then
    DB_PATH="${PROJECT_ROOT}/chroma_db"
fi

echo "  Books directory: $BOOKS_PATH"
echo "  Database directory: $DB_PATH"
echo "  Logs directory: ${PROJECT_ROOT}/logs"

# Create directories
mkdir -p "$BOOKS_PATH"
mkdir -p "$DB_PATH"
mkdir -p "${PROJECT_ROOT}/logs"

# Step 5: Generate configuration files
echo ""
echo -e "${BLUE}📌 Generating configuration files...${NC}"

export SPIRITUAL_LIBRARY_BOOKS_PATH="$BOOKS_PATH"
export SPIRITUAL_LIBRARY_DB_PATH="$DB_PATH"
export SPIRITUAL_LIBRARY_LOGS_PATH="${PROJECT_ROOT}/logs"

"${PROJECT_ROOT}/scripts/generate_configs.sh" >/dev/null 2>&1
echo -e "  ${GREEN}✓${NC} Configuration files generated"

# Step 6: Install service (macOS only, if requested)
if [[ "$OSTYPE" == "darwin"* ]] && [ "$INSTALL_SERVICE" = true ]; then
    echo ""
    echo -e "${BLUE}📌 Installing background service...${NC}"
    
    # Uninstall if exists
    if launchctl list | grep -q "com.spiritual-library.index-monitor" 2>/dev/null; then
        "${PROJECT_ROOT}/scripts/uninstall_service.sh" >/dev/null 2>&1
    fi
    
    # Install service
    "${PROJECT_ROOT}/scripts/install_service.sh" >/dev/null 2>&1
    echo -e "  ${GREEN}✓${NC} Index monitor service installed"
fi

# Step 7: Start web monitor (if requested)
if [ "$START_WEB_MONITOR" = true ]; then
    echo ""
    echo -e "${BLUE}📌 Starting web monitor...${NC}"
    
    # Kill existing monitor if running
    pkill -f monitor_web_enhanced 2>/dev/null || true
    
    # Start new monitor
    nohup "$venv_path/bin/python" "${PROJECT_ROOT}/src/monitoring/monitor_web_enhanced.py" \
        > "${PROJECT_ROOT}/logs/webmonitor_stdout.log" 2>&1 &
    
    echo -e "  ${GREEN}✓${NC} Web monitor started at http://localhost:8888"
fi

# Step 8: Initial indexing (if documents exist)
echo ""
echo -e "${BLUE}📌 Checking for documents to index...${NC}"

doc_count=$(find "$BOOKS_PATH" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.epub" -o -name "*.txt" \) 2>/dev/null | wc -l | tr -d ' ')

if [ "$doc_count" -gt 0 ]; then
    echo "  Found $doc_count documents"
    
    if [ "$INTERACTIVE" = true ]; then
        read -p "  Run initial indexing now? [Y/n]: " response
        response="${response:-y}"
        if [[ "$response" =~ ^[Yy]$ ]]; then
            RUN_INDEXING=true
        else
            RUN_INDEXING=false
        fi
    else
        RUN_INDEXING=true
    fi
    
    if [ "$RUN_INDEXING" = true ]; then
        echo "  Starting indexing..."
        cd "$PROJECT_ROOT"
        if [ -f "./scripts/run.sh" ]; then
            ./scripts/run.sh --index-only
        fi
    fi
else
    echo "  No documents found in $BOOKS_PATH"
fi

# Final summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Configuration:${NC}"
echo "  • Books: $BOOKS_PATH"
echo "  • Database: $DB_PATH"
echo "  • Logs: ${PROJECT_ROOT}/logs"
echo ""
echo -e "${CYAN}Quick Commands:${NC}"
echo "  • Run MCP server: ./scripts/run.sh"
echo "  • Index documents: ./scripts/run.sh --index-only"
echo "  • Check status: ./scripts/service_status.sh"

if [ "$START_WEB_MONITOR" = true ]; then
    echo "  • Web monitor: http://localhost:8888"
fi

echo ""
echo -e "${CYAN}Claude Desktop:${NC}"
echo "  Copy config from: ${PROJECT_ROOT}/config/claude_desktop_config.json"
echo "  To: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""

# Save environment file
cat > "${PROJECT_ROOT}/.env" << EOF
# Spiritual Library MCP Server Configuration
# Generated by setup.sh on $(date)

SPIRITUAL_LIBRARY_BOOKS_PATH="$BOOKS_PATH"
SPIRITUAL_LIBRARY_DB_PATH="$DB_PATH"
SPIRITUAL_LIBRARY_LOGS_PATH="${PROJECT_ROOT}/logs"
EOF

echo -e "${MAGENTA}Setup completed successfully!${NC}"