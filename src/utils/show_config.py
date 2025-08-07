#!/usr/bin/env python3
"""
Show current configuration for Personal Document Library MCP Server
Demonstrates how to use the config system
"""

import os
import sys
from src.core.config import config

def main():
    print("=== Personal Document Library MCP Server Configuration ===\n")
    
    # Show current configuration
    config_info = config.get_config_info()
    
    print("📁 Current Paths:")
    print(f"  Base Directory: {config_info['base_dir']}")
    print(f"  Books Directory: {config_info['books_directory']}")
    print(f"  Database Directory: {config_info['db_directory']}")
    print(f"  Logs Directory: {config_info['logs_directory']}")
    print()
    
    print("🔧 Environment Variables:")
    for var, value in config_info['environment_variables'].items():
        print(f"  {var}: {value}")
    print()
    
    print("📊 Directory Status:")
    for name, path in [
        ("Books", config.books_directory),
        ("Database", config.db_directory),
        ("Logs", config.logs_directory)
    ]:
        exists = "✅ Exists" if path.exists() else "❌ Missing"
        print(f"  {name}: {exists}")
    print()
    
    print("🔄 Configuration Options:")
    print(f"  To change books directory: export PERSONAL_LIBRARY_DOC_PATH='/path/to/books'")
    print(f"  To change database directory: export PERSONAL_LIBRARY_DB_PATH='/path/to/db'")
    print(f"  To change logs directory: export PERSONAL_LIBRARY_LOGS_PATH='/path/to/logs'")
    print()
    
    # Check if directories exist, create if needed
    try:
        config.ensure_directories()
        print("✅ All directories created successfully!")
    except Exception as e:
        print(f"❌ Error creating directories: {e}")
    
    # Show some example paths
    print("\n📚 Example Usage:")
    print("  from src.core.config import config")
    print("  books_path = config.books_directory")
    print("  db_path = config.db_directory")
    print("  # Or use the convenience functions:")
    print("  books_path = str(config.books_directory)")

if __name__ == "__main__":
    main()