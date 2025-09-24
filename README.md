# Personal Document Library MCP Server

A Model Context Protocol (MCP) server that enables Claude to access and analyze a personal collection of documents through RAG (Retrieval-Augmented Generation). The system processes PDFs, Word documents, EPUBs, and MOBI/Kindle ebooks locally, creates semantic search capabilities, and provides synthesis across multiple sources.

## Features

- **14 Powerful MCP Tools** for Claude integration
- **Local RAG System** with ChromaDB vector storage
- **Semantic Search** with book filtering and synthesis capabilities  
- **Background Monitoring** with automatic indexing service
- **Automatic PDF Cleaning** for problematic files
- **Web Dashboard** with real-time monitoring at http://localhost:8888
- **Enter Key Search** support in web interface
- **Lazy Initialization** for fast MCP startup
- **ARM64 Compatible** (Apple Silicon optimized)
- **Multi-format Support** (PDF, DOCX, DOC, PPTX, PPT, EPUB, MOBI, AZW, AZW3, TXT)
- **Calibre Integration** for MOBI/Kindle ebook conversion
- **Progress Tracking** with consistent status updates

## Quick Start

### Prerequisites

- **macOS** (tested on macOS 14+)
- **Python 3.12** (automatically installed if missing)
- **Claude Desktop** installed
- **Homebrew** (for package management)
- **~4GB RAM** for embeddings
- **coreutils** (provides gtimeout for service monitoring)

> **Important**: This setup requires Python 3.12 specifically. Python 3.13 is not currently supported due to ChromaDB incompatibility with numpy 2.0+. The setup scripts will automatically install Python 3.12 if it's not found on your system. All other dependencies including coreutils will also be installed automatically.

### Optional Dependencies (Auto-installed by setup)

- **ocrmypdf** - For OCR processing of scanned PDFs
- **LibreOffice** - For processing Word documents (.doc, .docx)
- **pandoc** - For EPUB file processing

### Installation

#### Option 0: Install as a Python package (New)

The project now ships as an installable Python package so you can bootstrap the tools without cloning the repository:

```bash
pip install personal-doc-library

# Create data directories and review configuration
pdlib-cli ensure-dirs
pdlib-cli config

# Launch services from anywhere on your system
pdlib-mcp            # Start the MCP server
pdlib-indexer        # Start the background index monitor
pdlib-webmonitor     # Run the Flask-based dashboard
```

If you plan to use advanced document conversion tooling or the optional service helpers, install the corresponding extras:

```bash
# Enable document-processing extras such as pandoc and unstructured
pip install "personal-doc-library[document-processing]"

# Add service helpers including python-daemon
pip install "personal-doc-library[services]"
```

Use `pdlib-cli --help` to explore additional utility commands (failed document recovery, indexing diagnostics, and more). The optional extras described below remain available if you need automated service installation or a fully scripted environment.

#### Option 1: Comprehensive Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/hpoliset/PersonalDocLibraryRAGMCP
cd PersonalDocLibraryRAGMCP

# Run comprehensive setup (with service installation)
./serviceInstall.sh
```

The `serviceInstall.sh` script provides a complete installation experience with background service setup:
- ✅ Check for Python 3.12 (installs it automatically if missing)
- ✅ Create/verify virtual environment
- ✅ Install all Python dependencies
- ✅ Auto-install system dependencies (ocrmypdf, LibreOffice, pandoc)
- ✅ Configure paths interactively or via command line
- ✅ Generate all configuration files
- ✅ Install background indexing service (optional)
- ✅ Install web monitor as service (optional)
- ✅ Run initial document indexing (optional)
- ✅ Save environment configuration

#### Option 2: Automated Setup

```bash
# Clone the repository
git clone https://github.com/hpoliset/PersonalDocLibraryRAGMCP
cd PersonalDocLibraryRAGMCP

# Run automated setup with all options
./serviceInstall.sh --books-path /path/to/your/books --install-service --start-web-monitor --non-interactive
```

Available `serviceInstall.sh` options:
- `--books-path PATH` - Path to your document library
- `--db-path PATH` - Path for vector database (default: ./chroma_db)
- `--non-interactive` - Run without prompts
- `--install-service` - Install background indexing service
- `--start-web-monitor` - Install web monitor as service
- `--help` - Show all available options

#### Option 3: Interactive Installation (Non-Service Mode)

```bash
# For interactive installation without background services
./install_interactive_nonservicemode.sh
```

Note: This script provides an interactive installation without setting up background services. Use `serviceInstall.sh` for a complete setup with services.

### Post-Installation

#### 1. Configure Claude Desktop

Copy the generated configuration to Claude Desktop:

```bash
# macOS
cp config/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop for changes to take effect
```

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
./scripts/service_status.sh
./scripts/webmonitor_service_status.sh

# Install services
./scripts/install_service.sh          # Index monitor
./scripts/install_webmonitor_service.sh # Web monitor

# Uninstall services
./scripts/uninstall_service.sh
./scripts/uninstall_webmonitor_service.sh

# View logs
tail -f logs/index_monitor_stdout.log
tail -f logs/webmonitor_stdout.log
```

## Usage

### Running the MCP Server

```bash
# Start MCP server (for Claude Desktop)
./scripts/run.sh

# Index documents only
./scripts/run.sh --index-only

# Index with retry for large collections
./scripts/run.sh --index-only --retry
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
PersonalDocLibraryRAGMCP/
├── books/              # Your document library (configurable)
├── chroma_db/          # Vector database storage
├── logs/               # Application logs
├── config/             # Configuration files
├── scripts/            # Utility scripts
├── src/                # Source code
│   ├── core/          # Core RAG functionality
│   ├── servers/       # MCP server implementation
│   ├── indexing/      # Document indexing
│   └── monitoring/    # Web dashboard
├── docs/               # Documentation and images
│   └── images/        # Screenshots for documentation
└── venv_mcp/          # Python 3.12 virtual environment
```

## MCP Tools Available in Claude

Once configured, Claude will have access to these 14 tools:

### Search & Discovery
1. **search** - Semantic search with optional book filtering and synthesis
2. **list_books** - List books by pattern, author, or directory
3. **recent_books** - Find recently indexed books by time period
4. **find_practices** - Find specific practices or techniques

### Content Extraction
5. **extract_pages** - Extract specific pages from any book
6. **extract_quotes** - Find notable quotes on specific topics
7. **summarize_book** - Generate AI summary of entire books

### Analysis & Synthesis
8. **compare_perspectives** - Compare perspectives across multiple sources
9. **question_answer** - Direct Q&A from your library
10. **daily_reading** - Get suggested passages for daily reading

### System Management
11. **library_stats** - Get library statistics and indexing status
12. **index_status** - Get detailed indexing progress
13. **refresh_cache** - Refresh search cache and reload book index
14. **warmup** - Initialize RAG system to prevent timeouts

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

### Running Tests
```bash
# Activate virtual environment
source venv_mcp/bin/activate

# Run tests (when available)
python -m pytest tests/
```

### Adding New Document Types

Edit `src/personal_doc_library/core/shared_rag.py` to add support for new formats:
1. Add file extension to `SUPPORTED_EXTENSIONS`
2. Implement loader in `load_document()`
3. Update categorization if needed

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

[Your License Here]

## Support

For issues or questions:
- Open an issue on GitHub
- Check logs in `logs/` directory
- Review `CLAUDE.md` for development details
- See `QUICK_REFERENCE.md` for command reference