# Changelog

All notable changes to the Spiritual Library MCP Server will be documented in this file.

## [2.1.0] - 2025-07-05

### Added
- **New Content Tools**: 
  - `summarize_book` - Generate AI summaries of entire books
  - `extract_quotes` - Find notable quotes on specific topics  
  - `daily_reading` - Get themed passages for daily practice
  - `question_answer` - Ask direct questions about teachings
- **ARM64 Compatibility**: Full Apple Silicon support with dedicated `venv_mcp`
- **Lazy Initialization**: Fast MCP startup, RAG loads only when tools are used
- **Proper MCP Protocol Compliance**: Fixed initialization response format
- **Enhanced Error Handling**: Proper JSON-RPC error responses

### Fixed
- **Architecture Mismatch**: Resolved x86_64 vs ARM64 issues on Apple Silicon
- **Embedding Dimension Mismatch**: Restored original 768-dim `all-mpnet-base-v2` model
- **MCP Timeout Issues**: Lazy initialization prevents 6-second startup delay
- **Search Functionality**: Now returns actual results instead of 0 passages
- **Server Disconnection**: Proper protocol flow keeps connection alive

### Changed
- **Embedding Model**: Switched from `all-MiniLM-L6-v2` (384-dim) to `all-mpnet-base-v2` (768-dim)
- **Virtual Environment**: Using `venv_mcp` with Homebrew Python for ARM64 compatibility
- **MCP Server Structure**: Complete rewrite with lazy loading and proper protocol handling

### Technical
- **Python Environment**: ARM64-native Python 3.11 via Homebrew
- **Vector Database**: ChromaDB with 768-dimensional embeddings
- **Performance**: ~1.75s search latency, supports synthesis across multiple sources
- **Monitoring**: Real-time web dashboard and comprehensive logging

## [2.0.0] - 2025-07-04

### Added
- **Hybrid Architecture**: Support for automatic, background, and manual indexing modes
- **Background Monitor Service**: Continuous monitoring with LaunchAgent support
- **Web Monitoring Interface**: Real-time status dashboard at localhost:8888
- **Enhanced Lock System**: File-based locking with stale detection and auto-cleanup
- **Automatic PDF Cleaning**: Ghostscript-based cleaning for problematic PDFs
- **Service Mode**: Install as system service with auto-restart capabilities

### Enhanced
- **Shared RAG System**: Common functionality between MCP server and background monitor
- **Error Recovery**: Automatic handling of corrupted or malformed PDFs
- **Content Categorization**: Improved classification into practice, energy_work, philosophy, general
- **Statistics Tracking**: Detailed library statistics and indexing history

## [1.0.0] - 2025-07-03

### Initial Release
- **Basic MCP Server**: Core Model Context Protocol implementation
- **RAG System**: PDF indexing with ChromaDB vector storage
- **Search Functionality**: Semantic search across spiritual library
- **Claude Integration**: Direct integration with Claude Desktop
- **PDF Processing**: Automatic text extraction and chunking
- **Synthesis Capabilities**: AI-powered synthesis across multiple sources

### Core Tools
- `search` - Semantic search with optional synthesis
- `find_practices` - Find specific spiritual practices
- `compare_perspectives` - Compare perspectives across sources
- `library_stats` - Get library statistics and indexing status

### Technical Foundation
- **Vector Storage**: ChromaDB with sentence-transformers embeddings
- **LLM Integration**: Ollama with llama3.1:70b model
- **PDF Processing**: PyPDF2 with recursive text splitting
- **Content Organization**: Metadata-based categorization system