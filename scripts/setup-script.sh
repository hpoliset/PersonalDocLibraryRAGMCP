#!/bin/bash

# Spiritual Library MCP Server Setup Script

echo "🔮 Spiritual Library MCP Server Setup"
echo "===================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher."
    exit 1
else
    echo "✅ Found $python_version"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📌 Creating virtual environment..."
    python3 -m venv venv
    if [[ $? -ne 0 ]]; then
        echo "❌ Error: Failed to create virtual environment."
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "📌 Activating virtual environment..."
source venv/bin/activate

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo ""
    echo "📌 Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
langchain==0.1.0
chromadb==0.4.22
sentence-transformers==2.2.2
fastapi==0.109.0
uvicorn==0.27.0
pypdf2==3.0.1
pydantic==2.5.3
EOF
    echo "✅ requirements.txt created"
fi

# Install dependencies
echo ""
echo "📌 Installing Python dependencies..."
echo "This may take a few minutes..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
if [[ $? -ne 0 ]]; then
    echo "❌ Error: Failed to install dependencies."
    exit 1
fi
# Install additional dependencies for multi-document support
pip install -q pypandoc "unstructured[all-docs]" "numpy<2.0"
echo "✅ All dependencies installed"

# Create books directory if it doesn't exist
if [ ! -d "books" ]; then
    echo ""
    echo "📌 Creating books directory..."
    mkdir books
    echo "✅ Created books directory"
    echo ""
    echo "📚 Please add your spiritual books (PDF format) to the ./books directory"
else
    # Count PDFs in books directory
    pdf_count=$(find books -name "*.pdf" -type f | wc -l)
    echo ""
    echo "✅ Books directory exists with $pdf_count PDF files"
fi

# Note: Ollama is no longer required
echo ""
echo "📌 The system now uses direct RAG results without LLM synthesis"
echo "✅ This reduces memory requirements from ~40GB to ~4GB"

# Create other necessary files if they don't exist
echo ""
echo "📌 Checking project files..."

# Create start_server.sh if it doesn't exist
if [ ! -f "start_server.sh" ]; then
    cat > start_server.sh << 'EOF'
#!/bin/bash
# Start the Spiritual Library MCP Server

echo "🔮 Starting Spiritual Library MCP Server..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "📌 Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Start the server
echo "📌 Starting MCP server on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""
python -m uvicorn mcp_server:app --reload --port 8000
EOF
    chmod +x start_server.sh
    echo "✅ Created start_server.sh"
fi

# Create claude_config.json if it doesn't exist
if [ ! -f "claude_config.json" ]; then
    current_dir=$(pwd)
    cat > claude_config.json << EOF
{
  "mcpServers": {
    "spiritual-library": {
      "command": "$current_dir/venv/bin/python",
      "args": ["-m", "uvicorn", "mcp_server:app", "--port", "8000"],
      "cwd": "$current_dir"
    }
  }
}
EOF
    echo "✅ Created claude_config.json with current directory path"
fi

echo ""
echo "✨ Setup Complete!"
echo "=================="
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Add your spiritual books (PDF format) to the ./books directory"
echo "   cp /path/to/your/books/*.pdf ./books/"
echo ""
echo "2. Create the Python files (rag_system.py, mcp_server.py, test_server.py)"
echo "   These should be provided with this setup script"
echo ""
echo "3. Start the server:"
echo "   ./start_server.sh"
echo ""
echo "4. Configure Claude Desktop:"
echo "   - Open ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "   - Add the contents from ./claude_config.json"
echo "   - Restart Claude Desktop"
echo ""
echo "5. Test the integration in Claude with:"
echo "   'Search my spiritual library for meditation techniques'"
echo ""
echo "For more information, see README.md"