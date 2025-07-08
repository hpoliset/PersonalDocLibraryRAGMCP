# Spiritual Library MCP Server

A Model Context Protocol (MCP) server that enables Claude to access and analyze a personal collection of spiritual books through RAG (Retrieval-Augmented Generation). The system processes PDFs locally, creates semantic search capabilities, and provides synthesis across multiple sources.

## Features

- **9 Powerful Tools** for Claude integration
- **Local RAG System** with ChromaDB vector storage
- **Semantic Search** with synthesis capabilities  
- **Background Monitoring** with automatic indexing
- **Automatic PDF Cleaning** for problematic files
- **Web Dashboard** for real-time monitoring
- **Lazy Initialization** for fast MCP startup
- **ARM64 Compatible** (Apple Silicon optimized)

## Quick Start

### 1. Prerequisites
- **macOS** (tested on macOS 14+)
- **Python 3.9+** (ARM64 version for Apple Silicon)
- **Claude Desktop** installed
- **Homebrew** for package management
- **~4GB RAM** for embeddings (vs 40GB for Ollama)

### 2. Install Dependencies
```bash
# Install required system packages
brew install python@3.11 ghostscript

# For Word document support (.doc and .docx files)
brew install --cask libreoffice

# For EPUB support  
brew install pandoc

# Install and start Ollama service (optional - no longer required)
# brew install ollama
# brew services start ollama
# ollama pull llama3.3:70b-instruct-q8_0
```

### 3. Setup Project
```bash
# Clone the repository
git clone <your-repo-url>
cd spiritual-library-mcp

# Run the setup script (creates venv_mcp with ARM64 Python)
./scripts/setup-script.sh

# Verify installation
python -c "import platform; print(f'Architecture: {platform.machine()}')"
```

### 4. Add Your Books
```bash
# Create books directory (if not exists)
mkdir -p books

# Place your spiritual books in the books directory
# Supported formats: PDF, Word (.docx, .doc), EPUB
cp your-spiritual-books/*.pdf books/
cp your-spiritual-books/*.docx books/
cp your-spiritual-books/*.epub books/

# Optional: Test PDF processing
python src/indexing/clean_pdfs.py
```

### 5. Configure Claude Desktop
Edit your Claude Desktop config file:
```bash
# Open the config file
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add this configuration (replace `/path/to/spiritual-library-mcp` with your actual path):
```json
{
  "mcpServers": {
    "spiritual-library": {
      "command": "/path/to/spiritual-library-mcp/venv_mcp/bin/python",
      "args": ["/path/to/spiritual-library-mcp/src/servers/mcp_complete_server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Critical Notes:**
- Use **absolute paths** (not relative paths like `./` or `~/`)
- Must use the `venv_mcp` virtual environment (ARM64 compatible)
- Include the `PYTHONUNBUFFERED` environment variable

### 6. Test Installation
```bash
# Test the server manually
./scripts/run.sh

# Should show: "Server is running and ready for queries"
# Press Ctrl+C to stop

# Test with Claude Desktop
# 1. Restart Claude Desktop
# 2. Open a new conversation
# 3. Ask: "What books do you have access to?"
```

### 7. Start Using
Just talk to Claude! Books are indexed automatically on first use.

## Available Tools

### Search & Analysis
- **search** - Semantic search with optional synthesis
- **find_practices** - Find specific spiritual practices  
- **compare_perspectives** - Compare perspectives across sources

### Content Tools  
- **summarize_book** - Generate AI summary of an entire book
- **extract_quotes** - Find notable quotes on a topic
- **daily_reading** - Get suggested passages for daily practice
- **question_answer** - Ask direct questions about teachings

### Status Tools
- **library_stats** - Get library statistics and status
- **index_status** - Get detailed indexing status

## Usage Modes

### Mode 1: Automatic (Recommended)
```bash
./scripts/run.sh
# Books indexed automatically when queried
```

### Mode 2: Background Monitoring  
```bash
./scripts/index_monitor.sh    # Start background monitor
./scripts/stop_monitor.sh     # Stop background monitor
# Books indexed instantly when added
```

### Mode 3: Manual Control
```bash
./scripts/run.sh --index-only  # Index now
./scripts/run.sh              # Then run server
```

## Architecture

- **MCP Server** (`mcp_complete_server.py`) - Full MCP protocol implementation
- **Shared RAG** (`shared_rag.py`) - Core RAG functionality with lock handling  
- **Index Monitor** (`index_monitor.py`) - Background indexing service
- **Web Monitor** (`src/monitoring/monitor_web_enhanced.py`) - Real-time dashboard

## Requirements

- **Python 3.9+** (ARM64 version recommended for Apple Silicon)
- **Ollama** with llama3.3:70b model (~40GB RAM required)
- **Ghostscript** for PDF cleaning (`brew install ghostscript`)
- **Claude Desktop** for MCP integration

## Technical Details

- **Vector Storage**: ChromaDB with 768-dimensional embeddings
- **Embedding Model**: `sentence-transformers/all-mpnet-base-v2`
- **Text Splitter**: Recursive character splitting (1000 chars, 200 overlap)
- **Content Categories**: practice, energy_work, philosophy, general
- **Lock System**: File-based with stale detection and auto-cleanup
- **Configuration**: Environment variable-based path configuration

## Monitoring

### Web Dashboard
```bash
python src/monitoring/monitor_web_enhanced.py
# Open http://localhost:8888
```

### Service Mode (Advanced)

Install both services to run automatically in the background:

```bash
# Install indexer service
./scripts/install_service.sh       # Install indexer as LaunchAgent
./scripts/service_status.sh        # Check indexer service health  
./scripts/uninstall_service.sh     # Remove indexer service

# Install web monitor service  
./scripts/install_webmonitor_service.sh     # Install web monitor as LaunchAgent
./scripts/webmonitor_service_status.sh      # Check web monitor service health
./scripts/uninstall_webmonitor_service.sh   # Remove web monitor service
```

**Service Features:**
- **Auto-start** at system boot
- **Auto-restart** if crashed
- **Background operation** with no terminal required
- **Comprehensive logging** in `logs/` directory

## Troubleshooting

### Common Issues

1. **MCP Server Not Connecting**
   ```bash
   # Check Ollama is running
   ollama list
   brew services list | grep ollama
   
   # Verify virtual environment
   /path/to/spiritual-library-mcp/venv_mcp/bin/python --version
   
   # Check Claude Desktop logs
   tail -f ~/Library/Logs/Claude/mcp-server-spiritual-library.log
   
   # Test server manually
   ./scripts/run.sh
   ```

2. **Search Returns No Results**
   ```bash
   # Check if books are indexed
   python -c "from shared_rag import SharedRAG; rag = SharedRAG(); print(rag.get_stats())"
   
   # Verify PDFs are in books directory
   ls -la books/
   
   # Check for indexing errors
   python clean_pdfs.py
   ```

3. **Architecture Mismatch (Apple Silicon)**
   ```bash
   # Check current architecture
   python -c "import platform; print(f'Architecture: {platform.machine()}')"
   
   # Recreate ARM64 virtual environment
   rm -rf venv_mcp
   /opt/homebrew/bin/python3.11 -m venv venv_mcp
   source venv_mcp/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **PDF Processing Errors**
   ```bash
   # Check for failed PDFs
   cat failed_pdfs.json
   
   # Clean problematic PDFs
   python clean_pdfs.py
   
   # Check Ghostscript installation
   which gs
   ```

5. **Port Already in Use**
   ```bash
   # Kill existing processes
   lsof -ti:8000 | xargs kill -9
   
   # Check for running monitors
   ps aux | grep monitor
   ```

### Step-by-Step Debugging

#### 1. Verify Prerequisites
```bash
# Check Python version and architecture
python --version
python -c "import platform; print(f'Architecture: {platform.machine()}')"

# Check Ollama
ollama --version
ollama list | grep llama3.3

# Check Ghostscript
gs --version
```

#### 2. Test Virtual Environment
```bash
# Activate and test
source venv_mcp/bin/activate
python -c "import chromadb, langchain, sentence_transformers; print('All imports successful')"
```

#### 3. Test RAG System
```bash
# Test core functionality
python -c "
from shared_rag import SharedRAG
rag = SharedRAG()
print('RAG system initialized successfully')
print(f'Stats: {rag.get_stats()}')
"
```

#### 4. Test MCP Server
```bash
# Run server manually
./scripts/run.sh

# In another terminal, test basic functionality
curl -X POST http://localhost:8000/health
```

#### 5. Verify Claude Desktop Integration
```bash
# Check Claude Desktop config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop
pkill -f "Claude Desktop"
open -a "Claude Desktop"
```

### Performance Optimization

#### For Large Libraries (100+ books)
```bash
# Use background monitoring
./scripts/install_service.sh
./scripts/service_status.sh

# Monitor indexing progress
python src/monitoring/monitor_web_enhanced.py
# Open http://localhost:8888
```

#### For Limited Memory Systems
```bash
# Use smaller LLM model
ollama pull llama3.1:8b-instruct-q8_0

# Edit shared_rag.py to use smaller model
# Change model_name to "llama3.1:8b-instruct-q8_0"
```

### Debug Commands
```bash
# Test server manually with verbose output
./scripts/run.sh

# Check library statistics
python -c "
from shared_rag import SharedRAG
rag = SharedRAG()
stats = rag.get_stats()
print(f'Books: {stats[\"books\"]}')
print(f'Chunks: {stats[\"chunks\"]}')
print(f'Categories: {stats[\"categories\"]}')
"

# Clean and reindex all PDFs
python clean_pdfs.py
rm -rf chroma_db/
./scripts/run.sh

# Check service status (if installed)
./scripts/service_status.sh

# View logs
tail -f logs/index_monitor_stdout.log    # Indexer service logs
tail -f logs/webmonitor_stdout.log       # Web monitor service logs

# View web monitoring
python src/monitoring/monitor_web_enhanced.py &
open http://localhost:8888
```

### Getting Help

If you're still having issues:

1. **Check the logs** - Most issues are visible in the logs
2. **Test manually** - Run `./scripts/run.sh` to see detailed output
3. **Check architecture** - Ensure ARM64 compatibility on Apple Silicon
4. **Verify paths** - Use absolute paths in Claude Desktop config
5. **Monitor resources** - Ensure sufficient RAM for Ollama (~40GB)

## Configuration

### Directory Paths
The system uses a flexible configuration system that supports environment variables:

```bash
# View current configuration
python show_config.py

# Customize paths via environment variables
export SPIRITUAL_LIBRARY_BOOKS_PATH="/custom/path/to/books"
export SPIRITUAL_LIBRARY_DB_PATH="/custom/path/to/database"
export SPIRITUAL_LIBRARY_LOGS_PATH="/custom/path/to/logs"

# Then restart the server
./scripts/run.sh
```

**Default paths** (relative to project directory):
- Books: `./books/`
- Database: `./chroma_db/`  
- Logs: `./logs/`

**Environment variables:**
- `SPIRITUAL_LIBRARY_BOOKS_PATH` - Override books directory
- `SPIRITUAL_LIBRARY_DB_PATH` - Override database directory
- `SPIRITUAL_LIBRARY_LOGS_PATH` - Override logs directory

### Git Configuration
The `books/` folder is automatically excluded from git to prevent committing large PDF files. Use environment variables to point to a shared books directory if needed.

## Development

### Adding New Tools
1. Add tool definition to `mcp_complete_server.py` in `tools/list` response
2. Implement handler in `tools/call` method  
3. Test with manual server run

### Modifying Search
Edit parameters in `shared_rag.py`:
- `chunk_size`: Text segment size (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 200)  
- `k`: Number of results (default: 10)

### Logging System

All services generate comprehensive logs in the `logs/` directory:

**Log Files:**
- `index_monitor_stdout.log` - Indexer service output
- `index_monitor_stderr.log` - Indexer service errors  
- `webmonitor_stdout.log` - Web monitor service output
- `webmonitor_stderr.log` - Web monitor service errors

**Viewing Logs:**
```bash
# Real-time log monitoring
tail -f logs/index_monitor_stdout.log    # Follow indexer output
tail -f logs/webmonitor_stdout.log       # Follow web monitor output

# Error investigation
tail -f logs/index_monitor_stderr.log    # Follow indexer errors
tail -f logs/webmonitor_stderr.log       # Follow web monitor errors

# Search logs
grep -i "error" logs/*.log               # Find all errors
grep -i "word" logs/index_monitor_stdout.log  # Find Word document processing
```

**Log Rotation:**
- Logs are automatically managed by macOS LaunchAgent
- Old logs are preserved for troubleshooting
- No manual cleanup required

**Log Levels:**
- `INFO` - Normal operation (indexing progress, status updates)
- `WARNING` - Non-critical issues (skipped files, retries)
- `ERROR` - Critical failures (processing errors, service failures)

### Configuration System
All components use the centralized config system in `config.py`:
```python
from config import config

# Access configured paths
books_path = config.books_directory
db_path = config.db_directory
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on [LangChain](https://langchain.com/) and [ChromaDB](https://www.trychroma.com/)
- Uses [Ollama](https://ollama.ai/) for local LLM inference
- Integrates with [Claude Desktop](https://claude.ai/) via Model Context Protocol