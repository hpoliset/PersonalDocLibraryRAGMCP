# Ragdex - RAG Document Indexer for MCP

[![PyPI Version](https://img.shields.io/pypi/v/ragdex.svg)](https://pypi.org/project/ragdex/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black.svg)](https://github.com/hpoliset/DocumentIndexerMCP)

**Ragdex** is a production-ready RAG (Retrieval-Augmented Generation) document indexer and search system for MCP (Model Context Protocol) that enables Claude to access and analyze your personal document collection. The system processes PDFs, Word documents, EPUBs, and MOBI/Kindle ebooks locally, creates semantic search capabilities, and provides synthesis across multiple sources.

## Features

- **17 Powerful MCP Tools** for Claude integration
- **5 Interactive Prompts** for common document analysis workflows
- **4 Dynamic Resources** for library statistics and configuration
- **Local RAG System** with ChromaDB vector storage (768-dim embeddings)
- **Semantic Search** with book filtering and synthesis capabilities
- **Background Monitoring** with automatic indexing service
- **Automatic PDF Cleaning** for problematic files
- **Web Dashboard** with real-time monitoring at http://localhost:8888
- **Python Package Distribution** via `ragdex` command-line tools
- **Lazy Initialization** for fast MCP startup (<1s)
- **ARM64 Compatible** (Apple Silicon optimized)
- **Multi-format Support** (PDF, DOCX, DOC, PPTX, PPT, EPUB, MOBI, AZW, AZW3, TXT)
- **Calibre Integration** for MOBI/Kindle ebook conversion
- **Progress Tracking** with consistent status updates

## Quick Start

### Prerequisites

- **Python 3.10+** (3.10, 3.11, or 3.12 supported)
- **Claude Desktop** or other MCP-compatible client
- **~4GB RAM** for embedding model
- **macOS** or **Linux** (Windows support coming soon)

> **Note**: Python 3.13 is not currently supported due to ChromaDB incompatibility with numpy 2.0+.

### Optional Dependencies (Auto-installed by setup)

- **ocrmypdf** - For OCR processing of scanned PDFs
- **LibreOffice** - For processing Word documents (.doc, .docx)
- **pandoc** - For EPUB file processing

### Installation

#### Option 1: Install from PyPI (Recommended)

```bash
# Using uv for faster installation (recommended)
uv venv ~/ragdex_env
cd ~/ragdex_env
uv pip install ragdex

# Or using standard pip
python -m venv ~/ragdex_env
source ~/ragdex_env/bin/activate
pip install ragdex

# With optional dependencies
pip install ragdex[document-processing,services]
```

#### Option 2: Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/hpoliset/DocumentIndexerMCP
cd DocumentIndexerMCP

# Install in editable mode with all dependencies
pip install -e .

# Or with optional extras
pip install -e ".[document-processing,services]"

# Create data directories and review configuration
ragdex ensure-dirs
ragdex config

# Launch services from anywhere on your system
ragdex-mcp            # Start the MCP server
ragdex-index          # Start the background index monitor
ragdex-web            # Run the web dashboard
```

#### Available CLI Commands

```bash
ragdex --help                        # Show all available commands
ragdex ensure-dirs                   # Create necessary directories
ragdex config                        # View current configuration
ragdex check-indexing-status         # Check document indexing status
ragdex find-unindexed                # Find documents not yet indexed
ragdex manage-failed-pdfs            # Manage failed document list
ragdex show-config                   # Display configuration details
```

### Quick Setup with Services (macOS)

```bash
# Install ragdex and services
uv venv ~/ragdex_env
cd ~/ragdex_env
uv pip install ragdex

# Download service installer scripts
curl -O https://raw.githubusercontent.com/hpoliset/DocumentIndexerMCP/main/install_ragdex_services.sh
curl -O https://raw.githubusercontent.com/hpoliset/DocumentIndexerMCP/main/uninstall_ragdex_services.sh
curl -O https://raw.githubusercontent.com/hpoliset/DocumentIndexerMCP/main/ragdex_status.sh
chmod +x *.sh

# Install services
./install_ragdex_services.sh

# Check status
./ragdex_status.sh
```

The service installer script provides:
- ✅ Automatic service installation for background indexing
- ✅ Web monitor dashboard at http://localhost:8888
- ✅ Automatic startup on system boot
- ✅ Log rotation and monitoring

### Post-Installation

#### 1. Configure Claude Desktop

Add ragdex to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "ragdex": {
      "command": "/Users/YOUR_USERNAME/ragdex_env/bin/ragdex-mcp",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "CHROMA_TELEMETRY": "false",
        "PERSONAL_LIBRARY_DOC_PATH": "/Users/YOUR_USERNAME/SpiritualLibrary",
        "PERSONAL_LIBRARY_DB_PATH": "/Users/YOUR_USERNAME/DocumentIndexerMCP/chroma_db",
        "PERSONAL_LIBRARY_LOGS_PATH": "/Users/YOUR_USERNAME/DocumentIndexerMCP/logs"
      }
    }
  }
}
```

Save this to: `~/Library/Application Support/Claude/claude_desktop_config.json`

Restart Claude Desktop for changes to take effect.

#### 2. Access Web Dashboard

Open http://localhost:8888 in your browser to access the comprehensive monitoring dashboard:

![Personal Document Library Monitor Dashboard](docs/images/RAGMCPWebMonitor.png)

**Dashboard Features:**
- 📊 **Real-time Status** - View indexing progress and system status
- 📚 **Library Statistics** - Track total books, chunks, and failed documents
- 🔍 **Smart Search** - Search by title, author, or category with Enter key support
- 📈 **Progress Tracking** - Monitor indexing with consistent status updates
- 📋 **Document Library** - Browse all indexed books with metadata
- ⚠️ **Failed Documents** - Track and manage problematic files
- 🔒 **Lock Status** - Monitor system locks and concurrent operations

## Services

### Background Services (macOS)

The system includes two LaunchAgent services that run automatically:

1. **Index Monitor Service** - Watches for new documents and indexes them
2. **Web Monitor Service** - Provides the web dashboard

#### Service Management

```bash
# Check service status
launchctl list | grep ragdex

# View logs
tail -f ~/DocumentIndexerMCP/logs/ragdex_indexer_stderr.log
tail -f ~/DocumentIndexerMCP/logs/ragdex_web_stderr.log

# Restart services
launchctl unload ~/Library/LaunchAgents/com.ragdex.*.plist
launchctl load ~/Library/LaunchAgents/com.ragdex.*.plist
```

## Usage

### Running the MCP Server

```bash
# If installed from PyPI
ragdex-mcp            # Start the MCP server
ragdex-index          # Start background indexing
ragdex-web            # Start web dashboard

# Or use the CLI
ragdex --help         # Show all available commands
```

### Manual Operations

```bash
# Start/stop web monitor manually
./scripts/start_web_monitor.sh
./scripts/stop_web_monitor.sh

# Check indexing status
./scripts/indexing_status.sh

# Monitor indexing progress continuously
watch -n 5 "./scripts/indexing_status.sh"

# Manage failed documents
./scripts/manage_failed_docs.sh list     # View failed documents
./scripts/manage_failed_docs.sh add      # Add document to skip list
./scripts/manage_failed_docs.sh remove   # Remove from skip list
./scripts/manage_failed_docs.sh retry    # Clear list to retry all
./scripts/cleanup_failed_list.sh         # Remove successfully indexed docs from failed list

# Pause/resume indexing
./scripts/pause_indexing.sh
./scripts/resume_indexing.sh
```

## Configuration

### Environment Variables

The system uses environment variables for configuration. These can be set in your shell or in the `.env` file:

```bash
# Books directory (where your PDFs/documents are stored)
export PERSONAL_LIBRARY_DOC_PATH="/path/to/your/books"

# Database directory (for vector storage)
export PERSONAL_LIBRARY_DB_PATH="/path/to/database"

# Logs directory
export PERSONAL_LIBRARY_LOGS_PATH="/path/to/logs"
```

### Directory Structure

```
~/ragdex_env/
├── books/                           # Your document library (configurable)
├── chroma_db/                       # Vector database storage
├── logs/                           # Application logs
├── config/                         # Configuration files
├── scripts/                        # Utility scripts
├── src/
│   └── personal_doc_library/       # Main package
│       ├── __init__.py
│       ├── cli.py                  # Command-line interface
│       ├── core/                   # Core RAG functionality
│       │   ├── config.py          # Configuration management
│       │   ├── shared_rag.py      # RAG implementation
│       │   └── logging_config.py  # Logging setup
│       ├── servers/                # MCP server implementation
│       │   └── mcp_complete_server.py
│       ├── indexing/               # Document indexing
│       │   ├── index_monitor.py   # Background monitoring
│       │   └── execute_indexing.py
│       ├── monitoring/             # Web dashboard
│       │   └── monitor_web_enhanced.py
│       └── utils/                  # Utility modules
├── docs/                           # Documentation and images
│   └── images/                     # Screenshots for documentation
├── pyproject.toml                  # Package configuration
└── venv_mcp/                       # Python 3.12 virtual environment
```

## MCP Protocol Features

### Tools (17 Available)

#### Search & Discovery
1. **search** - Semantic search with optional book filtering and synthesis
2. **list_books** - List books by pattern, author, or directory
3. **recent_books** - Find recently indexed books by time period
4. **find_practices** - Find specific practices or techniques

#### Content Extraction
5. **extract_pages** - Extract specific pages from any book
6. **extract_quotes** - Find notable quotes on specific topics
7. **summarize_book** - Generate AI summary of entire books

#### Analysis & Synthesis
8. **compare_perspectives** - Compare perspectives across multiple sources
9. **question_answer** - Direct Q&A from your library
10. **daily_reading** - Get suggested passages for daily reading

#### System Management
11. **library_stats** - Get library statistics and indexing status
12. **index_status** - Get detailed indexing progress
13. **refresh_cache** - Refresh search cache and reload book index
14. **warmup** - Initialize RAG system to prevent timeouts
15. **find_unindexed** - Find documents not yet indexed
16. **reindex_book** - Force reindex of specific book
17. **clear_failed** - Clear failed document list

### Prompts (5 Templates)

1. **analyze_theme** - Analyze a theme across your library
2. **compare_authors** - Compare writing styles and perspectives of authors
3. **extract_practices** - Extract practical techniques from books
4. **research_topic** - Deep research on a specific topic
5. **daily_wisdom** - Get daily wisdom from your library

### Resources (4 Dynamic)

1. **library://stats** - Current library statistics and metrics
2. **library://recent** - Recently indexed documents
3. **library://search-tips** - Search tips and query examples
4. **library://config** - Current configuration settings

## Troubleshooting

### Common Issues

#### Indexer Gets Stuck on Large/Corrupted PDFs
```bash
# Check which file is stuck
cat chroma_db/index_status.json

# Use the failed docs manager script
./scripts/manage_failed_docs.sh list                    # View all failed documents
./scripts/manage_failed_docs.sh add "path/to/file.pdf"  # Add to skip list
./scripts/manage_failed_docs.sh remove "file.pdf"       # Remove from skip list
./scripts/manage_failed_docs.sh retry                   # Clear list to retry all

# Or manually add to failed list
echo '{"path/to/file.pdf": {"error": "Manual skip", "cleaned": false}}' >> chroma_db/failed_pdfs.json

# Restart the service
./scripts/uninstall_service.sh
./scripts/install_service.sh
```

#### Missing Dependencies for Document Processing
```bash
# Check and install OCR support for scanned PDFs
which ocrmypdf || brew install ocrmypdf

# Check and install LibreOffice for Word documents
which soffice || brew install --cask libreoffice

# Check and install pandoc for EPUB files
which pandoc || brew install pandoc

# Verify installations
ocrmypdf --version
soffice --version
pandoc --version
```

#### "Too Many Open Files" Errors
```bash
# Check current limit
ulimit -n

# Increase file descriptor limit (temporary)
ulimit -n 4096

# For permanent fix on macOS, add to ~/.zshrc or ~/.bash_profile:
echo "ulimit -n 4096" >> ~/.zshrc

# Restart the indexing service
./scripts/uninstall_service.sh
./scripts/install_service.sh
```

#### Service Keeps Restarting
```bash
# Check service logs for crashes
tail -f logs/index_monitor_stderr.log

# Check for lock files
ls -la /tmp/spiritual_library_index.lock

# Remove stale lock (if older than 30 minutes)
rm /tmp/spiritual_library_index.lock

# Monitor service health
./scripts/service_status.sh
watch -n 5 "./scripts/service_status.sh"
```

#### Web Monitor Not Accessible
```bash
# Check if service is running
launchctl list | grep webmonitor

# Restart the service
./scripts/uninstall_webmonitor_service.sh
./scripts/install_webmonitor_service.sh

# Check logs
tail -f logs/webmonitor_stdout.log

# Verify port is not in use
lsof -i :8888
```

#### Indexing Not Working
```bash
# Check service status
./scripts/service_status.sh

# View error logs
tail -f logs/index_monitor_stderr.log

# Check indexing progress
./scripts/indexing_status.sh

# Manually reindex
./scripts/run.sh --index-only

# Reindex with retry for large collections
./scripts/run.sh --index-only --retry
```

#### Permission Issues
```bash
# Fix permissions for scripts
chmod +x scripts/*.sh

# Fix Python symlinks
./serviceInstall.sh --non-interactive

# Fix directory permissions
chmod -R 755 logs/
chmod -R 755 chroma_db/
```

#### Word Documents Not Processing
```bash
# Verify LibreOffice is installed
which soffice || brew install --cask libreoffice

# Test LibreOffice manually
soffice --headless --convert-to pdf test.docx

# Check for temporary lock files (start with ~$)
find books/ -name "~\$*" -delete
```

### Python Version Requirements

**This system requires Python 3.12 specifically.** The setup scripts will automatically install Python 3.12 via Homebrew if it's not found on your system. All scripts use Python 3.12 from the virtual environment (`venv_mcp`) directly, ensuring consistency across all components.

> **Note**: Python 3.13 is incompatible due to ChromaDB requiring numpy < 2.0, while Python 3.13 requires numpy ≥ 2.1.

### Reset and Clean

If you need to start fresh:

```bash
# Remove vector database
rm -rf chroma_db/*

# Uninstall services
./scripts/uninstall_service.sh
./scripts/uninstall_webmonitor_service.sh

# Reinstall
./serviceInstall.sh  # or ./install_interactive_nonservicemode.sh
```

## Document Support

### Supported Formats
- **PDF** (.pdf) - Including scanned PDFs with OCR
- **Word** (.docx, .doc) - Requires LibreOffice
- **PowerPoint** (.pptx, .ppt) - Requires LibreOffice
- **EPUB** (.epub) - Requires pandoc
- **MOBI/Kindle** (.mobi, .azw, .azw3) - Uses Calibre if available
- **Text** (.txt) - Plain text files

### Installing Optional Dependencies

For full document support:

```bash
# For Word documents
brew install --cask libreoffice

# For EPUB files
brew install pandoc

# For MOBI/Kindle ebooks
brew install --cask calibre

# For better PDF handling
brew install ghostscript
```

## Development

### Testing MCP Features

```bash
# Test MCP protocol implementation
python test_mcp_features.py

# Test resources functionality
python test_resources.py

# Activate virtual environment for development
source venv_mcp/bin/activate

# Run tests (when available)
python -m pytest tests/
```

### Adding New Document Types

Edit `src/personal_doc_library/core/shared_rag.py` to add support for new formats:
1. Add file extension to `SUPPORTED_EXTENSIONS`
2. Implement loader in `load_document()`
3. Update categorization if needed

### Package Development

```bash
# Install in editable mode
pip install -e .

# Build distribution
python -m build

# Run from module
python -m personal_doc_library.servers.mcp_complete_server
```

## Security Notes

- All processing is done locally - no data leaves your machine
- Database is stored locally in `chroma_db/`
- Services run with user permissions only
- No network access required except for web dashboard

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/hpoliset/DocumentIndexerMCP/issues)
- Check logs in `~/DocumentIndexerMCP/logs/` directory
- Review [Documentation](https://github.com/hpoliset/DocumentIndexerMCP/tree/main/docs)
- See `ragdex --help` for command reference