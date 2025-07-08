#!/bin/bash
echo "🚀 Spiritual Library Quick Start"
echo "================================"
echo ""

# Check architecture and set appropriate paths
ARCH=$(uname -m)
CPU_BRAND=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")

# Check if we're on Apple Silicon (even under Rosetta)
if [[ "$CPU_BRAND" == *"Apple"* ]] || [[ "$ARCH" == "arm64" ]]; then
    if [[ "$ARCH" == "x86_64" ]]; then
        echo "✅ Apple Silicon Mac detected (M4 Max running under Rosetta)"
        echo "   For optimal performance, consider using: arch -arm64 zsh"
    else
        echo "✅ Apple Silicon Mac detected"
    fi
    HOMEBREW_PREFIX="/opt/homebrew"
    PYTHON_HOMEBREW_PATH="/opt/homebrew/bin/python3.11"
elif [[ "$ARCH" == "x86_64" ]]; then
    echo "✅ Intel Mac detected"
    HOMEBREW_PREFIX="/usr/local"
    PYTHON_HOMEBREW_PATH="/usr/local/bin/python3.11"
else
    echo "❌ Error: Unsupported architecture: $ARCH"
    echo "   This script supports Intel (x86_64) and Apple Silicon (arm64) Macs"
    exit 1
fi

# Check for Homebrew
echo ""
echo "📌 Checking for Homebrew..."
if [ ! -d "$HOMEBREW_PREFIX" ]; then
    echo "❌ Homebrew not found at $HOMEBREW_PREFIX"
    echo "   Please install Homebrew first:"
    echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew installed but not in PATH"
    echo "   Run: eval $($HOMEBREW_PREFIX/bin/brew shellenv)"
    exit 1
fi

echo "✅ Homebrew found"

# Check and install system dependencies
echo ""
echo "📌 Checking system dependencies..."
deps_to_install=()

# Check Python installation with fallbacks
PYTHON_CMD=""
if command -v "$PYTHON_HOMEBREW_PATH" &> /dev/null; then
    PYTHON_CMD="$PYTHON_HOMEBREW_PATH"
    echo "✅ Python 3.11: Found at $PYTHON_HOMEBREW_PATH"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✅ Python 3.11: Found at $(which python3.11)"
elif command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | grep -o "3\.[0-9]\+")
    if [[ "$python_version" == "3.11" ]] || [[ "$python_version" == "3.10" ]] || [[ "$python_version" == "3.9" ]]; then
        PYTHON_CMD="python3"
        echo "✅ Python $python_version: Found at $(which python3)"
    elif [[ "$python_version" == "3.13" ]]; then
        echo "⚠️  Python $python_version found, but some packages require <3.13"
        echo "   Installing Python 3.11 via Homebrew for compatibility"
        deps_to_install+=("python@3.11")
        PYTHON_CMD="$PYTHON_HOMEBREW_PATH"
    else
        echo "⚠️  Python $python_version found, but 3.9-3.12 recommended"
        PYTHON_CMD="python3"
    fi
else
    deps_to_install+=("python@3.11")
    PYTHON_CMD="$PYTHON_HOMEBREW_PATH"
    echo "⚠️  Python 3.11 not found, will install via Homebrew"
fi


if ! command -v gs &> /dev/null; then
    deps_to_install+=("ghostscript")
else
    echo "✅ Ghostscript: Found"
fi

if ! command -v pandoc &> /dev/null; then
    deps_to_install+=("pandoc")
else
    echo "✅ Pandoc: Found"
fi

if ! command -v soffice &> /dev/null; then
    echo "⚠️  LibreOffice: Not found (needed for Word documents)"
    # Note: LibreOffice will be installed separately as it's a cask
    libreoffice_missing=true
else
    echo "✅ LibreOffice: Found"
    libreoffice_missing=false
fi

# Install missing dependencies
if [ ${#deps_to_install[@]} -ne 0 ]; then
    echo ""
    echo "📌 Installing missing dependencies: ${deps_to_install[*]}"
    brew install "${deps_to_install[@]}"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install system dependencies"
        echo "   Please manually install: ${deps_to_install[*]}"
        exit 1
    fi
    echo "✅ System dependencies installed"
    
    # Install LibreOffice if missing (needs to be installed as a cask)
    if [ "$libreoffice_missing" = true ]; then
        echo ""
        echo "📌 Installing LibreOffice (needed for Word document processing)..."
        brew install --cask libreoffice
        if [ $? -eq 0 ]; then
            echo "✅ LibreOffice installed successfully"
            
            # Verify installation
            if command -v soffice &> /dev/null; then
                echo "✅ LibreOffice soffice command available"
            else
                echo "⚠️  LibreOffice installed but soffice command not found"
                echo "   You may need to restart your terminal or add to PATH"
            fi
        else
            echo "⚠️  LibreOffice installation failed"
            echo "   Word document processing will not work"
            echo "   Try manually: brew install --cask libreoffice"
        fi
    fi
    
    # After installation, update PYTHON_CMD to actual location
    for dep in "${deps_to_install[@]}"; do
        if [[ "$dep" == "python@3.11" ]]; then
            # Check where Python 3.11 was actually installed
            if command -v "$PYTHON_HOMEBREW_PATH" &> /dev/null; then
                PYTHON_CMD="$PYTHON_HOMEBREW_PATH"
                echo "✅ Python 3.11 confirmed at: $PYTHON_HOMEBREW_PATH"
            elif command -v python3.11 &> /dev/null; then
                PYTHON_CMD="python3.11"
                echo "✅ Python 3.11 confirmed at: $(which python3.11)"
            elif command -v /usr/local/bin/python3.11 &> /dev/null; then
                PYTHON_CMD="/usr/local/bin/python3.11"
                echo "✅ Python 3.11 confirmed at: /usr/local/bin/python3.11"
            else
                echo "❌ Python 3.11 installation failed"
                exit 1
            fi
            break
        fi
    done
fi

# Configure books directory
echo ""
echo "📚 Configuring books directory..."
echo ""

# Check if books directory exists in export
if [ -d "books" ] && [ "$(find books -type f \( -name "*.pdf" -o -name "*.doc" -o -name "*.docx" -o -name "*.epub" \) | wc -l)" -gt 0 ]; then
    INCLUDED_BOOKS=true
    INCLUDED_COUNT=$(find books -type f \( -name "*.pdf" -o -name "*.doc" -o -name "*.docx" -o -name "*.epub" \) | wc -l)
else
    INCLUDED_BOOKS=false
    INCLUDED_COUNT=0
fi

echo "Options for your spiritual books:"
if [ "$INCLUDED_BOOKS" = true ]; then
    echo "  1) Use included books ($INCLUDED_COUNT documents found)"
    echo "  2) Use existing books directory on this Mac"
    echo "  3) Create new empty books directory"
else
    echo "  1) Use existing books directory on this Mac"
    echo "  2) Create new empty books directory"
fi

echo ""
read -p "Choose option: " books_choice

# Set books path based on choice
if [ "$INCLUDED_BOOKS" = true ]; then
    case $books_choice in
        1)
            BOOKS_PATH="$PWD/books"
            echo "✅ Using included books"
            ;;
        2)
            read -p "Enter full path to your books directory: " BOOKS_PATH
            # Expand tilde if present
            BOOKS_PATH="${BOOKS_PATH/#\~/$HOME}"
            ;;
        3)
            BOOKS_PATH="$PWD/books"
            mkdir -p "$BOOKS_PATH"
            echo "✅ Created new books directory"
            ;;
        *)
            BOOKS_PATH="$PWD/books"
            echo "✅ Using included books (default)"
            ;;
    esac
else
    case $books_choice in
        1)
            read -p "Enter full path to your books directory: " BOOKS_PATH
            # Expand tilde if present
            BOOKS_PATH="${BOOKS_PATH/#\~/$HOME}"
            ;;
        *)
            BOOKS_PATH="$PWD/books"
            mkdir -p "$BOOKS_PATH"
            echo "✅ Created new books directory"
            ;;
    esac
fi

# Verify books path exists
if [ ! -d "$BOOKS_PATH" ]; then
    echo "❌ Error: Books directory not found at $BOOKS_PATH"
    exit 1
fi

# Export environment variable
export SPIRITUAL_LIBRARY_BOOKS_PATH="$BOOKS_PATH"
echo ""
echo "📚 Books directory set to: $BOOKS_PATH"

# Count books
book_count=$(find "$BOOKS_PATH" -type f \( -name "*.pdf" -o -name "*.doc" -o -name "*.docx" -o -name "*.epub" \) 2>/dev/null | wc -l)
if [ $book_count -gt 0 ]; then
    echo "   Found $book_count documents:"
    echo "   - PDFs: $(find "$BOOKS_PATH" -name "*.pdf" 2>/dev/null | wc -l)"
    echo "   - Word: $(find "$BOOKS_PATH" \( -name "*.doc" -o -name "*.docx" \) 2>/dev/null | wc -l)"
    echo "   - EPUBs: $(find "$BOOKS_PATH" -name "*.epub" 2>/dev/null | wc -l)"
fi

# Add to shell profile
echo ""
echo "📌 Saving configuration..."
SHELL_PROFILE="$HOME/.zshrc"
if ! grep -q "SPIRITUAL_LIBRARY_BOOKS_PATH" "$SHELL_PROFILE" 2>/dev/null; then
    echo "export SPIRITUAL_LIBRARY_BOOKS_PATH=\"$BOOKS_PATH\"" >> "$SHELL_PROFILE"
    echo "✅ Added books path to $SHELL_PROFILE"
fi

# Create virtual environment
echo ""
echo "📌 Creating ARM64 virtual environment..."
if [ -d "venv_mcp" ]; then
    echo "   Removing existing virtual environment..."
    rm -rf venv_mcp
fi

"$PYTHON_CMD" -m venv venv_mcp
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    echo "   Please check that Python is properly installed"
    echo "   You can try manually with: $PYTHON_CMD -m venv venv_mcp"
    exit 1
fi
echo "✅ Virtual environment created"

# Check if requirements.txt exists, create if missing
if [ ! -f "requirements.txt" ]; then
    echo "📌 Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core dependencies
langchain==0.1.0
langchain-community==0.0.10
chromadb==0.4.22
sentence-transformers==2.2.2
pypdf2==3.0.1

# Document processing
pypandoc==1.12
unstructured[all-docs]==0.11.5
numpy<2.0

# Web monitoring
flask==3.0.0

# Utilities
python-dotenv==1.0.0
psutil==5.9.7
EOF
    echo "✅ requirements.txt created"
fi

# Activate and install packages
echo "📌 Installing Python packages..."
source venv_mcp/bin/activate
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python packages"
    echo "   This might be due to network issues or package conflicts"
    echo "   Try running: source venv_mcp/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Install additional dependencies for multi-document support
echo "📌 Installing additional document processing dependencies..."
pip install -q pypandoc "unstructured[all-docs]" "numpy<2.0"
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Some additional dependencies failed to install"
    echo "   Document processing may be limited"
else
    echo "✅ Additional dependencies installed"
fi

echo "✅ All packages installed"

# Create necessary directories
echo ""
echo "📌 Creating directories..."
mkdir -p logs chroma_db
echo "✅ Directories created"

# Generate Claude Desktop configuration
echo ""
echo "📌 Generating Claude Desktop configuration..."
CURRENT_DIR=$(pwd)
CLAUDE_CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

cat > claude_config.json << EOL
{
  "mcpServers": {
    "spiritual-library": {
      "command": "$CURRENT_DIR/venv_mcp/bin/python",
      "args": ["$CURRENT_DIR/src/servers/mcp_complete_server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "SPIRITUAL_LIBRARY_BOOKS_PATH": "$BOOKS_PATH"
      }
    }
  }
}
EOL

echo "✅ Configuration file created: claude_config.json"

# Final system validation
echo ""
echo "📌 Validating installation..."

# Test virtual environment and imports
if ! source venv_mcp/bin/activate 2>/dev/null; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Test critical imports
python -c "
import sys
print(f'Python version: {sys.version}')

# Test critical imports
try:
    import langchain
    import chromadb
    import sentence_transformers
    print('✅ Core dependencies: OK')
except ImportError as e:
    print(f'❌ Core import failed: {e}')
    sys.exit(1)

try:
    import pypandoc
    import numpy
    print('✅ Document processing dependencies: OK')
except ImportError as e:
    print('⚠️  Document processing may be limited:', e)

# Test LibreOffice availability
import subprocess
try:
    result = subprocess.run(['soffice', '--headless', '--version'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print('✅ LibreOffice: Available for Word document processing')
    else:
        print('⚠️  LibreOffice: Command failed, Word documents may not work')
except (subprocess.TimeoutExpired, FileNotFoundError):
    print('⚠️  LibreOffice: Not found, Word documents will not work')
    print('   Install with: brew install --cask libreoffice')

# Test MCP server structure
import os
if os.path.exists('src/servers/mcp_complete_server.py'):
    print('✅ MCP server structure: OK')
else:
    print('❌ MCP server structure: Missing')
    sys.exit(1)
" || {
    echo "❌ System validation failed"
    echo "   Please check the error messages above"
    exit 1
}

echo "✅ System validation complete"

# Final instructions
echo ""
echo "✅ Setup complete!"
echo "==============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure Claude Desktop:"
echo "   cp claude_config.json \"$CLAUDE_CONFIG_PATH\""
echo ""
echo "2. Restart Claude Desktop"
echo ""
if [ $book_count -gt 0 ]; then
    echo "3. Index your library ($book_count documents):"
    echo "   ./scripts/run.sh --index-only"
    echo ""
    echo "4. Monitor indexing progress:"
    echo "   python src/monitoring/monitor_web_enhanced.py"
    echo "   Open http://localhost:8888"
    echo ""
    echo "⏱  Estimated indexing time: $(( book_count * 2 / 60 )) - $(( book_count * 5 / 60 )) minutes"
else
    echo "3. Add books to: $BOOKS_PATH"
    echo ""
    echo "4. Then index your library:"
    echo "   ./scripts/run.sh --index-only"
fi
echo ""
echo "Your spiritual library is ready for Apple Silicon! 🎉"
