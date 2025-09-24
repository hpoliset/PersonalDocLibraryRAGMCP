#!/bin/bash

# Quick Start Script for Personal Document Library MCP Server
# Interactive setup that guides users through installation

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

# Parse command line arguments
AUTO_MODE=false
AUTO_BOOKS_PATH=""
AUTO_DB_PATH=""
AUTO_INSTALL_SERVICE=false
AUTO_START_WEB=false
AUTO_RUN_INDEX=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            AUTO_INSTALL_SERVICE=true
            AUTO_START_WEB=true
            AUTO_RUN_INDEX=true
            shift
            ;;
        --books-path)
            AUTO_BOOKS_PATH="$2"
            shift 2
            ;;
        --db-path)
            AUTO_DB_PATH="$2"
            shift 2
            ;;
        --no-service)
            AUTO_INSTALL_SERVICE=false
            shift
            ;;
        --no-web)
            AUTO_START_WEB=false
            shift
            ;;
        --no-index)
            AUTO_RUN_INDEX=false
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto                Run in automatic mode with defaults"
            echo "  --books-path PATH     Set books directory path"
            echo "  --db-path PATH        Set database directory path"
            echo "  --no-service          Don't install background service (with --auto)"
            echo "  --no-web              Don't start web monitor (with --auto)"
            echo "  --no-index            Don't run initial indexing (with --auto)"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  # Interactive setup (default)"
            echo "  ./quick_start.sh"
            echo ""
            echo "  # Fully automated with defaults"
            echo "  ./quick_start.sh --auto"
            echo ""
            echo "  # Automated with custom books path"
            echo "  ./quick_start.sh --auto --books-path /Users/me/Books"
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

clear
echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   📚 Personal Document Library MCP Server - Quick Start 📚║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Welcome! This script will help you set up the Personal Document Library MCP Server."
echo ""

# Function to prompt for yes/no
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    local response
    
    # In auto mode, always return yes for default=y questions
    if [ "$AUTO_MODE" = true ]; then
        if [ "$default" = "y" ]; then
            echo "  Auto: Yes"
            return 0
        else
            echo "  Auto: No"
            return 1
        fi
    fi
    
    if [ "$default" = "y" ]; then
        prompt="${prompt} [Y/n]: "
    else
        prompt="${prompt} [y/N]: "
    fi
    
    read -p "$prompt" response
    response="${response:-$default}"
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to prompt for directory path
prompt_directory() {
    local prompt="$1"
    local default="$2"
    local response
    
    # In auto mode, use default or provided path
    if [ "$AUTO_MODE" = true ]; then
        echo -e "  Auto: Using $default"
        echo "$default"
        return
    fi
    
    echo -e "${CYAN}$prompt${NC}"
    echo -e "Default: ${YELLOW}$default${NC}"
    read -p "Path (press Enter for default): " response
    
    if [ -z "$response" ]; then
        echo "$default"
    else
        # Expand ~ to home directory
        echo "${response/#\~/$HOME}"
    fi
}

# Check Python version
echo -e "${BLUE}📌 Checking system requirements...${NC}"
echo ""

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

# If Python 3.12 not found, offer to install it
if [ -z "$python_cmd" ]; then
    echo -e "  ${RED}✗${NC} Python 3.12 is required but not found"
    echo ""
    
    if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
        echo -e "${CYAN}Python 3.12 is required for ChromaDB compatibility${NC}"
        
        # In auto mode, install automatically; otherwise ask
        if [ "$AUTO_MODE" = true ]; then
            echo "  Auto: Installing Python 3.12 via Homebrew..."
            install_python=true
        elif prompt_yes_no "Install Python 3.12 via Homebrew?" "y"; then
            install_python=true
        else
            install_python=false
        fi
        
        if [ "$install_python" = true ]; then
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
            echo "  Please install Python 3.12 manually and try again"
            echo "  On macOS: brew install python@3.12"
            exit 1
        fi
    else
        echo "  Please install Python 3.12 and try again"
        echo "  On macOS: brew install python@3.12"
        exit 1
    fi
fi

# Check for virtual environment
echo ""
echo -e "${BLUE}📌 Setting up Python environment...${NC}"
echo ""

venv_path="${PROJECT_ROOT}/venv_mcp"

if [ -d "$venv_path" ]; then
    echo -e "  ${GREEN}✓${NC} Virtual environment found at: venv_mcp/"
else
    echo -e "  ${YELLOW}!${NC} Virtual environment not found"
    if prompt_yes_no "  Create virtual environment now?" "y"; then
        echo -n "  Creating virtual environment... "
        $python_cmd -m venv "$venv_path"
        echo -e "${GREEN}done${NC}"
    else
        echo -e "  ${RED}✗${NC} Virtual environment is required for installation"
        exit 1
    fi
fi

# Activate virtual environment
source "$venv_path/bin/activate"

# Fix Python symlinks if needed
if [ -L "$venv_path/bin/python" ]; then
    # Check if symlink is broken
    if [ ! -e "$venv_path/bin/python" ]; then
        echo "  Fixing Python symlinks..."
        cd "$venv_path/bin"
        rm -f python
        if [ -e python3.13 ]; then
            ln -s python3.13 python
        elif [ -e python3.12 ]; then
            ln -s python3.12 python
        elif [ -e python3.11 ]; then
            ln -s python3.11 python
        else
            ln -s python3 python
        fi
        cd "$PROJECT_ROOT"
    fi
fi

# Install dependencies
echo ""
echo -e "${BLUE}📌 Installing Python dependencies...${NC}"
echo ""

if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
    echo "  Installing core dependencies..."
    
    # First ensure pip is up to date
    "${venv_path}/bin/python" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1
    
    # Install dependencies with better error handling
    echo "  Installing langchain and document processing libraries..."
    "${venv_path}/bin/python" -m pip install --no-cache-dir \
        langchain==0.1.0 \
        langchain-community==0.0.10 \
        chromadb==0.4.22 \
        sentence-transformers \
        pypdf2==3.0.1 \
        pypandoc==1.12 2>/dev/null
    
    echo "  Installing additional document support..."
    "${venv_path}/bin/python" -m pip install --no-cache-dir \
        unstructured \
        python-docx \
        pypdf \
        openpyxl \
        pdfminer.six \
        python-dotenv \
        psutil \
        flask \
        'numpy<2.0' 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Dependencies installed successfully"
    else
        echo -e "  ${YELLOW}⚠️${NC} Some dependencies may have failed to install"
        echo "     You can try manual installation later with: pip install -r requirements.txt"
    fi
else
    echo -e "  ${YELLOW}⚠️${NC} requirements.txt not found"
fi

# Configure directories
echo ""
echo -e "${BLUE}📌 Configuring directories...${NC}"
echo ""

# Books directory - check for existing library first
if [ -n "$AUTO_BOOKS_PATH" ]; then
    default_books="$AUTO_BOOKS_PATH"
elif [ -d "/Users/${USER}/SpiritualLibrary" ]; then
    default_books="/Users/${USER}/SpiritualLibrary"
    echo -e "${GREEN}✓${NC} Found existing library at: $default_books"
elif [ -d "${HOME}/Documents/SpiritualLibrary" ]; then
    default_books="${HOME}/Documents/SpiritualLibrary"
    echo -e "${GREEN}✓${NC} Found existing library at: $default_books"
else
    default_books="${PROJECT_ROOT}/books"
fi

echo ""
if [ "$AUTO_MODE" = false ]; then
    echo -e "${CYAN}Where is your spiritual library located?${NC}"
    echo "This should be the folder containing your PDFs, Word docs, and EPUBs."
fi
BOOKS_PATH=$(prompt_directory "Books directory" "$default_books")

# Database directory  
echo ""
echo -e "${CYAN}Where do you want to store the vector database?${NC}"
default_db="${PROJECT_ROOT}/chroma_db"
DB_PATH=$(prompt_directory "Database directory" "$default_db")

# Create directories
echo ""
echo -n "Creating directories... "
mkdir -p "$BOOKS_PATH"
mkdir -p "$DB_PATH"
mkdir -p "${PROJECT_ROOT}/logs"
echo -e "${GREEN}done${NC}"

# Export environment variables
export PERSONAL_LIBRARY_DOC_PATH="$BOOKS_PATH"
export PERSONAL_LIBRARY_DB_PATH="$DB_PATH"
export PERSONAL_LIBRARY_LOGS_PATH="${PROJECT_ROOT}/logs"

# Generate configuration files
echo ""
echo -e "${BLUE}📌 Generating configuration files...${NC}"
echo ""
"${PROJECT_ROOT}/scripts/generate_configs.sh"

# Service installation (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo -e "${BLUE}📌 Service Installation${NC}"
    echo ""
    echo "The system can run background services to:"
    echo "  • Automatically index new documents"
    echo "  • Provide a web monitoring dashboard"
    echo ""
    
    if prompt_yes_no "Install background indexing service?" "y"; then
        echo "Installing index monitor service..."
        "${PROJECT_ROOT}/scripts/install_service.sh"
    fi
    
    if prompt_yes_no "Start web monitoring dashboard?" "y"; then
        echo "Starting web monitor on http://localhost:8888..."
        if [ "$USE_CENTRALIZED_CONFIG" = true ]; then
            nohup env PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
                "$PYTHON_CMD" -m personal_doc_library.monitoring.monitor_web_enhanced \
                > "${PROJECT_ROOT}/logs/webmonitor_stdout.log" 2>&1 &
        else
            nohup env PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
                "$venv_path/bin/python" -m personal_doc_library.monitoring.monitor_web_enhanced \
                > "${PROJECT_ROOT}/logs/webmonitor_stdout.log" 2>&1 &
        fi
        echo -e "${GREEN}✓${NC} Web monitor started"
    fi
fi

# Claude Desktop configuration
echo ""
echo -e "${BLUE}📌 Claude Desktop Integration${NC}"
echo ""

claude_config_dir="$HOME/Library/Application Support/Claude"
if [ -d "$claude_config_dir" ]; then
    echo "Claude Desktop detected."
    if prompt_yes_no "Configure Claude Desktop to use this MCP server?" "y"; then
        claude_config_file="$claude_config_dir/claude_desktop_config.json"
        
        if [ -f "$claude_config_file" ]; then
            echo -e "${YELLOW}⚠️  Existing Claude config found${NC}"
            echo "Please manually merge the configuration from:"
            echo "  ${PROJECT_ROOT}/config/claude_desktop_config.json"
        else
            cp "${PROJECT_ROOT}/config/claude_desktop_config.json" "$claude_config_file"
            echo -e "${GREEN}✓${NC} Claude Desktop configured"
            echo ""
            echo -e "${YELLOW}Note: Restart Claude Desktop for changes to take effect${NC}"
        fi
    fi
else
    echo "Claude Desktop not found. You can manually configure it later using:"
    echo "  ${PROJECT_ROOT}/config/claude_desktop_config.json"
fi

# Initial indexing
echo ""
echo -e "${BLUE}📌 Document Indexing${NC}"
echo ""

if [ -d "$BOOKS_PATH" ]; then
    # Count documents
    doc_count=$(find "$BOOKS_PATH" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.epub" -o -name "*.txt" \) 2>/dev/null | wc -l)
    
    if [ "$doc_count" -gt 0 ]; then
        echo "Found $doc_count documents in: $BOOKS_PATH"
        if prompt_yes_no "Run initial indexing now?" "y"; then
            echo "Starting indexing (this may take a while)..."
            
            # Export environment variables for indexing
            export PERSONAL_LIBRARY_DOC_PATH="$BOOKS_PATH"
            export PERSONAL_LIBRARY_DB_PATH="$DB_PATH"
            
            # Run indexing with proper Python path
            if [ -f "${PROJECT_ROOT}/scripts/run.sh" ]; then
                cd "$PROJECT_ROOT"
                ./scripts/run.sh --index-only
            else
                "$venv_path/bin/python" -c "
import sys
sys.path.append('${PROJECT_ROOT}/src')
from personal_doc_library.core.shared_rag import SharedRAG

print('Initializing RAG system...')
rag = SharedRAG('$BOOKS_PATH', '$DB_PATH')

print('Starting document indexing...')
results = rag.index_all_documents()
print(f'Indexing complete: {results}')
"
            fi
        fi
    else
        echo "No documents found in: $BOOKS_PATH"
        echo "Add your PDF, Word, or EPUB files there and run:"
        echo "  ./scripts/run.sh --index-only"
    fi
else
    echo "Books directory doesn't exist: $BOOKS_PATH"
    echo "Creating directory..."
    mkdir -p "$BOOKS_PATH"
fi

# Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📚 Configuration Summary:${NC}"
echo "  • Books directory: $BOOKS_PATH"
echo "  • Database directory: $DB_PATH"
echo "  • Logs directory: ${PROJECT_ROOT}/logs"
echo ""
echo -e "${CYAN}🚀 Quick Commands:${NC}"
echo "  • Run MCP server: ./scripts/run.sh"
echo "  • Index documents: ./scripts/run.sh --index-only"
echo "  • Check status: ./scripts/service_status.sh"
echo "  • Web monitor: http://localhost:8888"
echo ""
echo -e "${CYAN}📖 Documentation:${NC}"
echo "  • README.md - Getting started guide"
echo "  • QUICK_REFERENCE.md - Command reference"
echo "  • Claude.md - Project documentation"
echo ""

# Save configuration summary
cat > "${PROJECT_ROOT}/.env" << EOF
# Personal Document Library MCP Server Configuration
# Generated by quick_start.sh on $(date)

PERSONAL_LIBRARY_DOC_PATH="$BOOKS_PATH"
PERSONAL_LIBRARY_DB_PATH="$DB_PATH"
PERSONAL_LIBRARY_LOGS_PATH="${PROJECT_ROOT}/logs"
EOF

echo -e "${MAGENTA}Thank you for using Personal Document Library MCP Server!${NC}"
echo ""