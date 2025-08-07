#!/usr/bin/env python3
"""
Logging configuration for Personal Document Library system
Provides centralized logging setup with rotation and formatting
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

def setup_logging(
    name: str,
    log_dir: str = "logs",
    level: int = logging.INFO,
    console: bool = True,
    file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 7,
    format_string: str = None
):
    """
    Set up logging with both console and file handlers
    
    Args:
        name: Logger name (e.g., 'mcp_server', 'indexing')
        log_dir: Directory for log files
        level: Logging level
        console: Enable console output
        file: Enable file output
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep
        format_string: Custom format string
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if needed
    if file:
        Path(log_dir).mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Default format
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file:
        # Create filename with date
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{log_dir}/{name}_{timestamp}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_mcp_logging():
    """Set up logging specifically for MCP server"""
    return setup_logging(
        name='mcp_server',
        format_string='%(asctime)s - [%(levelname)s] - %(funcName)s - %(message)s'
    )

def setup_indexing_logging():
    """Set up logging specifically for indexing operations"""
    return setup_logging(
        name='indexing',
        format_string='%(asctime)s - [%(levelname)s] - %(message)s'
    )

def setup_monitor_logging():
    """Set up logging specifically for monitoring"""
    return setup_logging(
        name='monitor',
        console=False,  # Only file output for monitor
        format_string='%(asctime)s - %(message)s'
    )

# Performance logging utilities
class PerformanceLogger:
    """Helper class for logging performance metrics"""
    def __init__(self, logger):
        self.logger = logger
        self.timers = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        import time
        self.timers[operation] = time.time()
        self.logger.debug(f"Started: {operation}")
    
    def end_timer(self, operation: str, log_level=logging.INFO):
        """End timing and log the duration"""
        import time
        if operation in self.timers:
            duration = time.time() - self.timers[operation]
            self.logger.log(log_level, f"Completed: {operation} ({duration:.2f}s)")
            del self.timers[operation]
            return duration
        return 0
    
    def log_memory(self, message: str = "Memory usage"):
        """Log current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.logger.info(f"{message}: {memory_mb:.0f} MB")
        except ImportError:
            pass

# Example usage
if __name__ == "__main__":
    # Test the logging setup
    logger = setup_mcp_logging()
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    
    # Test performance logging
    perf = PerformanceLogger(logger)
    perf.start_timer("test_operation")
    import time
    time.sleep(0.1)
    perf.end_timer("test_operation")
    perf.log_memory()