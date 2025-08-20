#!/bin/bash

# Comprehensive Setup Script for Personal Document Library MCP Server
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

# Source centralized Python environment configuration if it exists
if [ -f "$SCRIPT_DIR/scripts/python_env.sh" ]; then
    source "$SCRIPT_DIR/scripts/python_env.sh"
    USE_CENTRALIZED_CONFIG=true
else
    USE_CENTRALIZED_CONFIG=false
fi

echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     📚 Personal Document Library MCP Server - Setup 📚    ║"
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

# Step 1: Check Python and system dependencies
echo -e "${BLUE}📌 Checking system requirements...${NC}"

# Check Python and version
python_cmd=""
python_version=""

# First check for Python 3.12 specifically
if command -v python3.12 &> /dev/null; then
    python_version=$(python3.12 --version 2>&1 | cut -d' ' -f2)
    echo -e "  ${GREEN}✓${NC} Python 3.12 found: $python_version"
    python_cmd="python3.12"
elif command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    major_version=$(echo $python_version | cut -d'.' -f1)
    minor_version=$(echo $python_version | cut -d'.' -f2)
    
    if [[ "$major_version" == "3" && "$minor_version" == "12" ]]; then
        echo -e "  ${GREEN}✓${NC} Python 3.12 found: $python_version"
        python_cmd="python3"
    elif [[ "$major_version" == "3" && "$minor_version" -gt "12" ]]; then
        echo -e "  ${YELLOW}⚠️${NC} Python $python_version found, but Python 3.12 is required (3.13+ not supported by ChromaDB)"
        python_cmd=""
    else
        echo -e "  ${YELLOW}⚠️${NC} Python $python_version found, but Python 3.12 is required"
        python_cmd=""
    fi
elif command -v python &> /dev/null; then
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    if [[ "$python_version" == 3.12.* ]]; then
        echo -e "  ${GREEN}✓${NC} Python 3.12 found: $python_version"
        python_cmd="python"
    fi
fi

# If Python 3.12 not found, try to install it
if [ -z "$python_cmd" ]; then
    echo -e "  ${RED}✗${NC} Python 3.12 is required but not found"
    
    if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
        echo -e "  ${CYAN}Python 3.12 is required for ChromaDB compatibility${NC}"
        
        # In interactive mode, ask for confirmation
        if [ "$INTERACTIVE" = true ]; then
            read -p "  Install Python 3.12 via Homebrew? [Y/n]: " response
            response="${response:-y}"
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                echo "  Please install Python 3.12 manually and try again"
                exit 1
            fi
        else
            # In non-interactive mode, automatically install
            echo "  Automatically installing Python 3.12 via Homebrew..."
        fi
        
        # Install Python 3.12
        echo "  Installing Python 3.12..."
        brew install python@3.12 >/dev/null 2>&1
        
        # Verify installation
        if command -v python3.12 &> /dev/null; then
            python_cmd="python3.12"
            python_version=$(python3.12 --version 2>&1 | cut -d' ' -f2)
            echo -e "  ${GREEN}✓${NC} Python 3.12 installed successfully: $python_version"
        else
            echo -e "  ${RED}✗${NC} Failed to install Python 3.12"
            echo "  Please install it manually: brew install python@3.12"
            exit 1
        fi
    else
        echo "  Please install Python 3.12 and try again"
        echo "  On macOS: brew install python@3.12"
        exit 1
    fi
fi

# Check for Homebrew (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo -e "  ${YELLOW}⚠️${NC} Homebrew not found. Some features may not work."
        echo "    Install from: https://brew.sh"
    else
        echo -e "  ${GREEN}✓${NC} Homebrew found"
    fi
    
    # Check for OCR tool
    if ! command -v ocrmypdf &> /dev/null; then
        echo -e "  ${YELLOW}⚠️${NC} ocrmypdf not found (needed for scanned PDFs)"
        if command -v brew &> /dev/null; then
            if [ "$INTERACTIVE" = true ]; then
                read -p "    Install ocrmypdf? [Y/n]: " response
                response="${response:-y}"
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    echo "    Installing ocrmypdf..."
                    brew install ocrmypdf >/dev/null 2>&1 && echo -e "    ${GREEN}✓${NC} ocrmypdf installed"
                fi
            else
                # Auto-install in non-interactive mode
                echo "    Auto-installing ocrmypdf..."
                brew install ocrmypdf >/dev/null 2>&1 && echo -e "    ${GREEN}✓${NC} ocrmypdf installed"
            fi
        fi
    else
        echo -e "  ${GREEN}✓${NC} ocrmypdf found"
    fi
    
    # Check for LibreOffice
    if ! command -v soffice &> /dev/null; then
        echo -e "  ${YELLOW}⚠️${NC} LibreOffice not found (needed for Word docs)"
        if command -v brew &> /dev/null && [ "$INTERACTIVE" = true ]; then
            read -p "    Install LibreOffice? [Y/n]: " response
            response="${response:-y}"
            if [[ "$response" =~ ^[Yy]$ ]]; then
                echo "    Installing LibreOffice..."
                brew install --cask libreoffice >/dev/null 2>&1 && echo -e "    ${GREEN}✓${NC} LibreOffice installed"
            fi
        fi
    else
        echo -e "  ${GREEN}✓${NC} LibreOffice found"
    fi
    
    # Check for pandoc
    if ! command -v pandoc &> /dev/null; then
        echo -e "  ${YELLOW}⚠️${NC} pandoc not found (needed for EPUB files)"
        if command -v brew &> /dev/null; then
            if [ "$INTERACTIVE" = true ]; then
                read -p "    Install pandoc? [Y/n]: " response
                response="${response:-y}"
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    echo "    Installing pandoc..."
                    brew install pandoc >/dev/null 2>&1 && echo -e "    ${GREEN}✓${NC} pandoc installed"
                fi
            else
                # Auto-install in non-interactive mode
                echo "    Auto-installing pandoc..."
                brew install pandoc >/dev/null 2>&1 && echo -e "    ${GREEN}✓${NC} pandoc installed"
            fi
        fi
    else
        echo -e "  ${GREEN}✓${NC} pandoc found"
    fi
    
    # Check for coreutils (provides gtimeout)
    if ! command -v gtimeout &> /dev/null; then
        echo -e "  ${YELLOW}⚠️${NC} coreutils not found (provides gtimeout for service monitoring)"
        if command -v brew &> /dev/null; then
            if [ "$INTERACTIVE" = true ]; then
                read -p "    Install coreutils? [Y/n]: " response
                response="${response:-y}"
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    echo "    Installing coreutils..."
                    brew install coreutils >/dev/null 2>&1 && echo -e "    ${GREEN}✓${NC} coreutils installed"
                fi
            else
                # Auto-install in non-interactive mode
                echo "    Auto-installing coreutils..."
                brew install coreutils >/dev/null 2>&1 && echo -e "    ${GREEN}✓${NC} coreutils installed"
            fi
        fi
    else
        echo -e "  ${GREEN}✓${NC} coreutils found"
    fi
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
    watchdog \
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

export PERSONAL_LIBRARY_DOC_PATH="$BOOKS_PATH"
export PERSONAL_LIBRARY_DB_PATH="$DB_PATH"
export PERSONAL_LIBRARY_LOGS_PATH="${PROJECT_ROOT}/logs"

"${PROJECT_ROOT}/scripts/generate_configs.sh" >/dev/null 2>&1
echo -e "  ${GREEN}✓${NC} Configuration files generated"

# Step 6: Install service (macOS only, if requested)
if [[ "$OSTYPE" == "darwin"* ]] && [ "$INSTALL_SERVICE" = true ]; then
    echo ""
    echo -e "${BLUE}📌 Installing background service...${NC}"
    
    # Uninstall if exists
    if launchctl list | grep -q "com.personal-library.index-monitor" 2>/dev/null; then
        "${PROJECT_ROOT}/scripts/uninstall_service.sh" >/dev/null 2>&1
    fi
    
    # Install service
    "${PROJECT_ROOT}/scripts/install_service.sh" >/dev/null 2>&1
    echo -e "  ${GREEN}✓${NC} Index monitor service installed"
fi

# Step 7: Install web monitor service (if requested)
if [ "$START_WEB_MONITOR" = true ]; then
    echo ""
    echo -e "${BLUE}📌 Installing web monitor service...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Kill existing monitor if running
        pkill -f monitor_web_enhanced 2>/dev/null || true
        
        # Check if service script exists
        if [ -f "${PROJECT_ROOT}/scripts/install_webmonitor_service.sh" ]; then
            # Install as service
            "${PROJECT_ROOT}/scripts/install_webmonitor_service.sh" >/dev/null 2>&1
            echo -e "  ${GREEN}✓${NC} Web monitor service installed"
            echo -e "  ${GREEN}✓${NC} Dashboard available at http://localhost:8888"
        else
            # Fallback to background process
            nohup "$venv_path/bin/python" "${PROJECT_ROOT}/src/monitoring/monitor_web_enhanced.py" \
                > "${PROJECT_ROOT}/logs/webmonitor_stdout.log" 2>&1 &
            echo -e "  ${GREEN}✓${NC} Web monitor started at http://localhost:8888"
        fi
    else
        # Non-macOS: run as background process
        nohup "$venv_path/bin/python" "${PROJECT_ROOT}/src/monitoring/monitor_web_enhanced.py" \
            > "${PROJECT_ROOT}/logs/webmonitor_stdout.log" 2>&1 &
        echo -e "  ${GREEN}✓${NC} Web monitor started at http://localhost:8888"
    fi
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
# Personal Document Library MCP Server Configuration
# Generated by setup.sh on $(date)

PERSONAL_LIBRARY_DOC_PATH="$BOOKS_PATH"
PERSONAL_LIBRARY_DB_PATH="$DB_PATH"
PERSONAL_LIBRARY_LOGS_PATH="${PROJECT_ROOT}/logs"
EOF

echo -e "${MAGENTA}Setup completed successfully!${NC}"