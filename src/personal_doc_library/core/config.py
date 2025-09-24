#!/usr/bin/env python3
"""
Configuration module for Personal Document Library MCP Server
Centralizes all configurable paths and settings
"""

import os
from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir, user_log_dir

# Discover project/package layout for legacy defaults
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT.parent
REPO_ROOT: Optional[Path] = None
if SRC_ROOT.name == "src":
    candidate = SRC_ROOT.parent
    if (candidate / ".git").exists():
        REPO_ROOT = candidate

# Environment variable names
ENV_BOOKS_PATH = "PERSONAL_LIBRARY_DOC_PATH"
ENV_DB_PATH = "PERSONAL_LIBRARY_DB_PATH"
ENV_LOGS_PATH = "PERSONAL_LIBRARY_LOGS_PATH"

APP_NAME = "personal_doc_library"
APP_AUTHOR = "pdlib"

USER_DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
USER_LOG_DIR = Path(user_log_dir(APP_NAME, APP_AUTHOR))


def _legacy_path(relative: str) -> Optional[Path]:
    if REPO_ROOT is None:
        return None
    legacy = (REPO_ROOT / relative).resolve()
    if legacy.exists():
        return legacy
    return None


def _default_books_path() -> Path:
    return _legacy_path("books") or (USER_DATA_DIR / "books")


def _default_db_path() -> Path:
    return _legacy_path("chroma_db") or (USER_DATA_DIR / "chroma_db")


def _default_logs_path() -> Path:
    return _legacy_path("logs") or USER_LOG_DIR

class Config:
    """Configuration class with environment variable support"""
    
    @property
    def books_directory(self) -> Path:
        """Get the books directory path"""
        path = os.getenv(ENV_BOOKS_PATH)
        default_path = _default_books_path()
        target = Path(path).expanduser() if path else default_path
        return target.resolve()
    
    @property
    def db_directory(self) -> Path:
        """Get the database directory path"""
        path = os.getenv(ENV_DB_PATH)
        default_path = _default_db_path()
        target = Path(path).expanduser() if path else default_path
        return target.resolve()
    
    @property
    def logs_directory(self) -> Path:
        """Get the logs directory path"""
        path = os.getenv(ENV_LOGS_PATH)
        default_path = _default_logs_path()
        target = Path(path).expanduser() if path else default_path
        return target.resolve()
    
    def ensure_directories(self):
        """Create directories if they don't exist"""
        for directory in [self.books_directory, self.db_directory, self.logs_directory]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_config_info(self) -> dict:
        """Get configuration information for debugging"""
        return {
            "package_root": str(PACKAGE_ROOT),
            "user_data_dir": str(USER_DATA_DIR),
            "user_log_dir": str(USER_LOG_DIR),
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
