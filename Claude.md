# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ragdex** is a production-ready MCP (Model Context Protocol) server that enables Claude to access and analyze a personal collection of documents and emails through RAG (Retrieval-Augmented Generation). The system supports multiple document formats (PDFs, Word documents, EPUBs, MOBI/AZW/AZW3 ebooks) and email archives (Apple Mail EMLX, Outlook OLM), featuring automatic indexing, real-time monitoring, smart filtering, and robust error handling.

**Current Status**: ✅ **FULLY OPERATIONAL** v0.2.0 with ARM64 compatibility, 768-dim embeddings, 17 MCP tools, email support, and smart filtering.

## Repository Structure

```
ragdex/
├── src/personal_doc_library/  # Main source code
│   ├── core/              # Core functionality (shared_rag.py, config.py, logging)
│   ├── servers/           # MCP server implementation
│   ├── indexing/          # Document indexing tools
│   ├── loaders/           # Email loaders (EMLX, Outlook)
│   ├── monitoring/        # Web monitoring interface
│   └── utils/             # Utility scripts
├── scripts/               # Shell scripts for running the system
├── tests/                 # Test files
├── config/                # Configuration templates
├── logs/                 # Log files (gitignored)
├── books/                # Document library (gitignored)
├── chroma_db/            # Vector database (gitignored)
└── docs/                 # Documentation files
```

## Architecture Overview

The system follows a **modular, service-oriented architecture**:

1. **MCP Complete Server** (`src/personal_doc_library/servers/mcp_complete_server.py`): Main MCP server with 17 tools
2. **Shared RAG System** (`src/personal_doc_library/core/shared_rag.py`): Core RAG functionality with vector storage
3. **Index Monitor** (`src/personal_doc_library/indexing/index_monitor.py`): Background service for automatic indexing
4. **Web Monitor** (`src/personal_doc_library/monitoring/monitor_web_enhanced.py`): Real-time dashboard (localhost:8888) with Enter key search support
5. **Configuration System** (`src/personal_doc_library/core/config.py`): Centralized path and settings management

### MCP Tools Available (17 total)
- **search**: Search library with optional book/email filtering and synthesis
- **find_practices**: Find specific practices or techniques
- **compare_perspectives**: Compare perspectives across sources
- **library_stats**: Get library statistics and indexing status
- **index_status**: Get detailed indexing status
- **summarize_book**: Generate AI summary of a book
- **extract_quotes**: Find notable quotes on topics
- **daily_reading**: Get suggested daily passages
- **question_answer**: Direct Q&A from library
- **refresh_cache**: Refresh search cache and reload index
- **warmup**: Initialize RAG system to prevent timeouts
- **list_books**: List books by pattern/author/directory
- **recent_books**: Find recently indexed books
- **extract_pages**: Extract specific pages from books
- **find_book_by_metadata**: Search by title/author/publisher
- **get_book_metadata**: Get detailed book metadata
- **search_by_date_range**: Search within date ranges

### Key Architectural Patterns
- **Lazy Loading**: RAG system initialized only when needed to avoid MCP timeouts
- **File-based Locking**: Cross-process coordination with 30-minute stale lock detection
- **Event-Driven Processing**: File system events trigger automatic indexing
- **Batch Processing**: Documents chunked and processed efficiently
- **Circuit Breaker**: 15-minute timeout protection for long operations

## Essential Commands

```bash
# Initial setup
./install_interactive_nonservicemode.sh  # Interactive setup (non-service mode)
./serviceInstall.sh              # Complete setup with service installation
pip install -r requirements.txt # Install dependencies (if manual setup)

# Running the system
./scripts/run.sh                # Run MCP server (default mode)
./scripts/run.sh --index-only   # Index documents only
./scripts/run.sh --index-only --retry  # Index with retry and memory monitoring

# Service management
./scripts/install_service.sh    # Install as LaunchAgent service
./scripts/service_status.sh     # Check service health
./scripts/uninstall_service.sh  # Remove service

# Background monitoring
./scripts/index_monitor.sh      # Start background monitor
./scripts/stop_monitor.sh       # Stop background monitor

# Web monitoring
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"
python -m personal_doc_library.monitoring.monitor_web_enhanced  # Start web dashboard (http://localhost:8888)

# Debugging
./scripts/test_logs.sh          # Test log viewing
./scripts/view_mcp_logs.sh      # View MCP server logs
./scripts/indexing_status.sh    # Check indexing status
```

## Claude Desktop Configuration

**Critical**: Must use `venv_mcp` virtual environment with absolute paths:

```json
{
  "mcpServers": {
    "personal-library": {
      "command": "/path/to/your/ragdex/venv_mcp/bin/python",
      "args": ["-m", "personal_doc_library.servers.mcp_complete_server"],
      "env": {
        "PYTHONPATH": "/path/to/your/ragdex/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Development Guidelines

### Python Environment
- **MUST use `venv_mcp`** (ARM64 virtual environment) for MCP server
- **Always use `venv_mcp/bin/python`** instead of plain python for indexing
- Python 3.9+ required (3.11 recommended)

### Document Processing Pipeline
1. **Discovery**: Scan directory for supported formats (PDF, Word, EPUB, MOBI/AZW/AZW3)
2. **Hash Checking**: MD5 comparison for change detection
3. **Processing**: Document → Loader → Text Extraction → Chunking → Categorization → Embedding → Vector Storage
4. **Error Handling**: Timeout protection, automatic PDF cleaning, failed document tracking, MOBI conversion via Calibre

### Vector Storage Details
- **Model**: sentence-transformers/all-mpnet-base-v2 (768-dimensional)
- **Database**: ChromaDB with persistent storage
- **Chunking**: 1200 characters with 150 character overlap
- **Categories**: practice, energy_work, philosophy, general

### Testing
- **No formal test suite exists** - high-priority contribution area
- **Manual testing**: Use `./scripts/run.sh` and monitoring tools
- Always test changes before committing

## Known Issues and Solutions

### LaunchAgent Permissions (macOS)
- **Issue**: LaunchAgent services restricted by sandboxing
- **Solution**: Use shell script wrapper (`scripts/index_monitor_service.sh`)
- **Details**: See `docs/LAUNCHAGENT_PERMISSIONS_SOLUTION.md`

### Common Troubleshooting
- If indexing finds 0 documents, check CloudDocs permissions
- For "Empty content" errors, documents may need cleaning
- Stale locks automatically cleaned after 30 minutes

## Environment Variables

- `PERSONAL_LIBRARY_DOC_PATH` - Override books directory
- `PERSONAL_LIBRARY_DB_PATH` - Override database directory  
- `PERSONAL_LIBRARY_LOGS_PATH` - Override logs directory

## Best Practices

1. **Always check existing code** before creating new files
2. **Prefer editing** existing files over creating new ones
3. **Use absolute paths** in all configurations
4. **Test before committing** - no commits until testing complete
5. **Follow existing patterns** - check neighboring files for conventions
6. **No documentation files** unless explicitly requested