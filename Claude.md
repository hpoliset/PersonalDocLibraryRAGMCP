# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Spiritual Library MCP Server** - a production-ready Model Context Protocol server that enables Claude to access and analyze a personal collection of spiritual documents through RAG (Retrieval-Augmented Generation). The system supports multiple document formats (PDFs, Word documents, EPUBs) and is now a complete git repository with professional infrastructure.

**Current Status**: ✅ **FULLY OPERATIONAL** with ARM64 compatibility, 768-dim embeddings, all 9 tools working, and multi-document support (PDF, Word, EPUB).

## Repository Structure

The codebase is organized as follows:
```
AITools/
├── src/                    # Main source code
│   ├── core/              # Core functionality (shared_rag, config, logging)
│   ├── servers/           # MCP server implementation
│   ├── indexing/          # PDF indexing tools
│   ├── monitoring/        # Web monitoring interface
│   └── utils/             # Utility scripts
├── scripts/               # Shell scripts for running the system
├── tests/                 # Test files
├── config/                # Configuration templates
├── logs/                 # Log files (gitignored)
├── books/                # PDF library (gitignored)
├── chroma_db/            # Vector database (gitignored)
├── backup/               # Legacy/backup files
└── docs/                 # Documentation files
```

This is now a complete git repository with:
- **Professional documentation** (README, CONTRIBUTING, CHANGELOG, PROJECT_STRUCTURE)
- **GitHub infrastructure** (CI/CD, issue templates, PR templates)
- **MIT License** with proper attribution
- **Comprehensive testing** setup across Python 3.9-3.11

## Architecture (v2.1 - Current)

The system follows a **modular, service-oriented architecture** with these core components:

1. **MCP Complete Server** (`src/servers/mcp_complete_server.py`): Production MCP server with 9 tools, lazy initialization, ARM64 compatible
2. **Shared RAG System** (`src/core/shared_rag.py`): Core functionality with 768-dim embeddings, lock handling, multi-document support (PDFs, Word docs, EPUBs), automatic PDF cleaning
3. **Index Monitor** (`src/indexing/index_monitor.py`): Background service with LaunchAgent support
4. **Web Monitor** (`src/monitoring/monitor_web_enhanced.py`): Real-time dashboard at localhost:8888
5. **Configuration System** (`src/core/config.py`): Centralized path and settings management
6. **Utilities** (`src/indexing/clean_pdfs.py`, scripts/): Supporting tools and automation

### Key Architectural Patterns
- **Lazy Loading**: RAG system initialized only when needed to avoid timeouts
- **File-based Locking**: Cross-process coordination with stale lock detection
- **Event-Driven Processing**: File system events trigger automatic indexing
- **Batch Processing**: Document chunks processed in efficient batches
- **Circuit Breaker**: Timeout protection for long operations

## Essential Commands

```bash
# Initial setup (one-time)
./quick_start.sh                # Interactive setup script (recommended)
./scripts/setup-script.sh       # Alternative setup script

# Choose your usage mode:

## Mode 1: Automatic (Default - Recommended for most users)
./scripts/run.sh
# Just use Claude - indexing happens automatically when needed

## Mode 2: Background Monitoring (For power users)
./scripts/index_monitor.sh    # Start background monitor
./scripts/stop_monitor.sh     # Stop background monitor
# Books are indexed instantly when added

## Mode 3: Manual Control
./scripts/run.sh --index-only  # Index now
./scripts/run.sh              # Then run server

## Service Mode: Install as System Service (Advanced)
./scripts/install_service.sh   # Install and start as LaunchAgent
./scripts/service_status.sh    # Check service health and status
./scripts/uninstall_service.sh # Stop and remove service
# Note: Uses shell script wrapper for proper CloudDocs permissions

## Web Monitoring Interface
python src/monitoring/monitor_web_enhanced.py  # Open http://localhost:8888
# Real-time status and statistics (read-only)

## Development and Testing
# No formal test suite exists yet - testing is done manually
./scripts/run.sh                # Test MCP server functionality
./scripts/test_logs.sh          # Test log viewing functionality
python src/monitoring/monitor_web_enhanced.py  # Test web monitoring
```

## Deployment Options - Hybrid Approach

The system uses a hybrid approach optimized for both automatic operation and manual control:

### 1. Claude Desktop Configuration (CURRENT - WORKING)

✅ **Current working configuration**:
```json
{
  "mcpServers": {
    "spiritual-library": {
      "command": "/Users/KDP/AITools/venv_mcp/bin/python",
      "args": ["/Users/KDP/AITools/src/servers/mcp_complete_server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Critical Requirements**:
- **MUST use `venv_mcp`** (ARM64 virtual environment)
- **MUST use absolute paths** in configuration
- **MUST include `PYTHONUNBUFFERED`** for proper logging

**Workflow Notes**:
- **Always use venv_mcp/python** when running the MCP server
- **Always use venv_mcp/bin/python instead of plain python**

**Benefits:**
- Server starts automatically when you query the spiritual library
- New documents are indexed on first use after adding them (supports PDFs, Word docs, EPUBs)
- No background resource usage when not in use
- Fresh process each time ensures clean state

**Indexing Guidelines**:
- **CORRECTION:** Always use `venv_mcp/bin/python` instead of plain python for indexer

## Development Notes

### Document Processing Pipeline
1. **Discovery**: Walk directory tree for supported formats (PDF, Word, EPUB)
2. **Hash Checking**: MD5 comparison for change detection
3. **Processing Flow**: Document → Loader → Text Extraction → Chunking → Categorization → Embedding → Vector Storage
4. **Error Handling**: Timeout protection, automatic PDF cleaning, failed document tracking

### Vector Storage and Embeddings
- **Model**: sentence-transformers/all-mpnet-base-v2 (768-dimensional)
- **Vector Store**: ChromaDB with persistent storage
- **Chunking**: 1200 characters with 150 character overlap
- **Categories**: practice, energy_work, philosophy, general

### Testing Strategy
- **No formal test suite** exists yet - this is a high-priority contribution area
- **Manual testing** approach using scripts and monitoring tools
- **Testing commands**: Use `./scripts/run.sh` to test MCP server, `./scripts/test_logs.sh` for log testing

### Python Environment Requirements
- **MUST use `venv_mcp`** (ARM64 virtual environment) for MCP server
- **Always use `venv_mcp/bin/python`** instead of plain python for indexer
- Using regular python for webmonitor is acceptable if setup that way originally

## Troubleshooting Notes

### Known Issues
- Do not try to fix "Empty content issues causing "Expected IDs to be a non-empty list" errors"

### LaunchAgent Service Issues (RESOLVED)
- **Issue**: LaunchAgent services finding 0 documents while manual execution finds 8,000+ documents
- **Root Cause**: macOS LaunchAgent sandboxing restricts direct Python access to CloudDocs directories
- **Solution**: Use LaunchAgent → Shell Script → Python architecture (see `docs/LAUNCHAGENT_PERMISSIONS_SOLUTION.md`)
- **Key Learning**: Shell scripts inherit full user permissions when launched by LaunchAgent, bypassing sandboxing
- **Implementation**: Service wrapper at `scripts/index_monitor_service.sh` provides proper environment and permissions

## Version Control Guidelines
- **Code Commit Guidelines**:
  - Don't commit any changes until testing is completed.

## Web Monitoring Guidelines
- **Always use the shell script to run the webmonitor. Run the python script only for debugging purposes if you suspect issues with the shell script**

## Ethics and Consent Guidelines
- **Consent Management**:
  - Don't use Rosetta without taking explicit consent.

## Best Practices
- Before creating any new script check if something similar exists