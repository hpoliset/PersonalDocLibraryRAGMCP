#!/usr/bin/env python3
"""
Configuration module for Spiritual Library MCP Server
Centralizes all configurable paths and settings
"""

import os
from pathlib import Path

# Base directory - project root (two levels up from this file)
BASE_DIR = Path(__file__).parent.parent.parent.absolute()

# Environment variable names
ENV_BOOKS_PATH = "SPIRITUAL_LIBRARY_BOOKS_PATH"
ENV_DB_PATH = "SPIRITUAL_LIBRARY_DB_PATH"
ENV_LOGS_PATH = "SPIRITUAL_LIBRARY_LOGS_PATH"

# Default paths (relative to BASE_DIR)
DEFAULT_BOOKS_PATH = BASE_DIR / "books"
DEFAULT_DB_PATH = BASE_DIR / "chroma_db"
DEFAULT_LOGS_PATH = BASE_DIR / "logs"

class Config:
    """Configuration class with environment variable support"""
    
    @property
    def books_directory(self) -> Path:
        """Get the books directory path"""
        env_path = os.getenv(ENV_BOOKS_PATH)
        default_path = str(DEFAULT_BOOKS_PATH)
        path = env_path if env_path else default_path
        
        # Debug logging for troubleshooting service issues
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Config DEBUG - ENV_BOOKS_PATH: {ENV_BOOKS_PATH}")
        logger.info(f"Config DEBUG - env_path: {env_path}")
        logger.info(f"Config DEBUG - default_path: {default_path}")
        logger.info(f"Config DEBUG - selected path: {path}")
        
        result = Path(path).expanduser().resolve()
        logger.info(f"Config DEBUG - resolved path: {result}")
        return result
    
    @property
    def db_directory(self) -> Path:
        """Get the database directory path"""
        path = os.getenv(ENV_DB_PATH, str(DEFAULT_DB_PATH))
        return Path(path).expanduser().resolve()
    
    @property
    def logs_directory(self) -> Path:
        """Get the logs directory path"""
        path = os.getenv(ENV_LOGS_PATH, str(DEFAULT_LOGS_PATH))
        return Path(path).expanduser().resolve()
    
    def ensure_directories(self):
        """Create directories if they don't exist"""
        for directory in [self.books_directory, self.db_directory, self.logs_directory]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_config_info(self) -> dict:
        """Get configuration information for debugging"""
        return {
            "base_dir": str(BASE_DIR),
            "books_directory": str(self.books_directory),
            "db_directory": str(self.db_directory),
            "logs_directory": str(self.logs_directory),
            "environment_variables": {
                ENV_BOOKS_PATH: os.getenv(ENV_BOOKS_PATH, "Not set"),
                ENV_DB_PATH: os.getenv(ENV_DB_PATH, "Not set"),
                ENV_LOGS_PATH: os.getenv(ENV_LOGS_PATH, "Not set")
            }
        }

# Global configuration instance
config = Config()

# Convenience functions for backward compatibility
def get_books_directory() -> str:
    """Get books directory as string"""
    return str(config.books_directory)

def get_db_directory() -> str:
    """Get database directory as string"""
    return str(config.db_directory)

def get_logs_directory() -> str:
    """Get logs directory as string"""
    return str(config.logs_directory)

if __name__ == "__main__":
    # Print current configuration
    import json
    print("Current Configuration:")
    print(json.dumps(config.get_config_info(), indent=2))
    
    # Ensure directories exist
    config.ensure_directories()
    print("\nDirectories created successfully!")