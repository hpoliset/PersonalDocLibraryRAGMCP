# Personal Document Library MCP Server - Setup Information

## System Requirements
- **Apple Silicon Mac (M1/M2/M3) ONLY**
- macOS 12.0 or later
- Homebrew installed at /opt/homebrew

## Repository Export Information
- Export Date: Tue Jul  8 22:44:47 IST 2025
- Source Machine: MacBook-Pro-M4-64.local
- Architecture: x86_64
- Git Branch: fix-search-revert
- Latest Commit: fec7644 feat: Add periodic lock update mechanism to prevent stale lock detection

## Setup Instructions for Apple Silicon Mac

### 1. Prerequisites
Install Homebrew if not already installed:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Extract and Setup
```bash
# Extract the archive
tar -xzf spiritual-library-mcp-*.tar.gz
cd spiritual-library-export

# Run the quick setup
./install_interactive_nonservicemode.sh
```

### 3. Configure Books Location
The setup will ask you where your spiritual books are located. You can:
- Use books included in this export (if exported with books)
- Point to an existing books directory
- Create a new empty books directory

### 4. Complete Setup
Follow the instructions from install_interactive_nonservicemode.sh to:
- Configure Claude Desktop
- Start indexing your library
- Monitor progress

## What's Included
- Complete source code (logs excluded)
- MCP server implementation
- Multi-document support (PDF, Word, EPUB)
- Web monitoring interface
- Background indexing service
- All scripts and utilities
- Books (if you chose to include them)

## What's NOT Included
- Log files (automatically excluded)
- Vector database (will be created on first run)
- Virtual environment (will be created by setup script)
- Temporary files
- Failed document records

## Environment Variables
The system uses these environment variables for flexibility:
- PERSONAL_LIBRARY_DOC_PATH - Location of your books
- PERSONAL_LIBRARY_DB_PATH - Vector database location
- PERSONAL_LIBRARY_LOGS_PATH - Log files location

## Support
This export is specifically for Apple Silicon Macs (ARM64).
Intel Mac (x86_64) support is not included.
