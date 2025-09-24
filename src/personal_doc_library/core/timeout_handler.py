"""
Improved timeout handler using subprocess for reliable process termination.
This solves the zombie thread problem while maintaining good performance.
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import pickle
import psutil
import logging
from pathlib import Path
from typing import Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class SubprocessTimeoutHandler:
    """
    Handles document processing with reliable timeout using subprocess.
    This ensures processes can be forcefully terminated, preventing zombies.
    """
    
    def __init__(self, max_cpu_percent=50, max_memory_percent=50):
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        
    def process_with_timeout(
        self,
        func_module: str,
        func_name: str, 
        args: tuple,
        timeout_seconds: int,
        progress_file: Optional[str] = None
    ) -> tuple[bool, Any]:
        """
        Execute a function in a subprocess with timeout.
        
        Args:
            func_module: Module containing the function
            func_name: Name of the function to execute
            args: Arguments to pass to the function
            timeout_seconds: Timeout in seconds
            progress_file: Optional file to monitor progress
            
        Returns:
            (success, result) tuple
        """
        
        # Create temporary files for data exchange
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pkl') as input_file:
            input_path = input_file.name
            pickle.dump({
                'module': func_module,
                'function': func_name,
                'args': args,
                'progress_file': progress_file
            }, input_file)
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pkl') as output_file:
            output_path = output_file.name
        
        # Python code to run in subprocess
        subprocess_code = f'''
import sys
import pickle
import importlib
import traceback

# Load input data
with open("{input_path}", "rb") as f:
    data = pickle.load(f)

# Import the module and get the function
try:
    module = importlib.import_module(data["module"])
    func = getattr(module, data["function"])
    
    # Execute the function
    result = func(*data["args"])
    
    # Save result
    with open("{output_path}", "wb") as f:
        pickle.dump({{"success": True, "result": result}}, f)
        
except Exception as e:
    # Save error
    with open("{output_path}", "wb") as f:
        pickle.dump({{"success": False, "error": str(e), "traceback": traceback.format_exc()}}, f)
'''
        
        # Start the subprocess
        start_time = time.time()
        last_progress_time = start_time
        last_progress_value = None
        extensions_granted = 0
        no_progress_window = 300  # 5 minutes without progress = kill
        
        try:
            # Run with initial timeout
            process = subprocess.Popen(
                [sys.executable, "-c", subprocess_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Monitor with adaptive timeout
            while True:
                elapsed = time.time() - start_time
                
                # Check if process is still running
                if process.poll() is not None:
                    # Process finished
                    break
                
                # Check system resources
                if not self._check_resource_limits():
                    logger.warning("Resource limits exceeded, terminating process")
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                    return False, "Resource limits exceeded"
                
                # Check progress if progress file provided
                if progress_file and os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r') as f:
                            progress_data = json.load(f)
                            current_progress = (
                                progress_data.get('current_page') or 
                                progress_data.get('chunks_generated') or 
                                0
                            )
                            
                            if current_progress != last_progress_value:
                                # Progress detected
                                logger.info(f"Progress: {current_progress}")
                                last_progress_value = current_progress
                                last_progress_time = time.time()
                    except:
                        pass
                
                # Check for timeout
                time_since_progress = time.time() - last_progress_time
                
                if elapsed > timeout_seconds:
                    # Check if we should extend
                    if time_since_progress < no_progress_window:
                        # Recent progress, extend timeout
                        extensions_granted += 1
                        extension_time = min(900, timeout_seconds // 2)  # Max 15 min extension
                        timeout_seconds += extension_time
                        logger.info(
                            f"Extension #{extensions_granted} granted: "
                            f"+{extension_time/60:.0f} min (total: {timeout_seconds/60:.0f} min)"
                        )
                    else:
                        # No recent progress, terminate
                        logger.error(f"No progress for {time_since_progress/60:.1f} minutes, terminating")
                        process.terminate()
                        time.sleep(2)
                        if process.poll() is None:
                            process.kill()
                        return False, f"Timeout after {elapsed/60:.1f} minutes"
                
                # Also check for stalled process
                if time_since_progress > no_progress_window:
                    logger.error(f"Process stalled (no progress for {no_progress_window/60:.0f} min)")
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                    return False, "Process stalled"
                
                # Wait a bit before next check
                time.sleep(2)
            
            # Process finished, get result
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    result_data = pickle.load(f)
                    
                if result_data['success']:
                    return True, result_data['result']
                else:
                    logger.error(f"Process failed: {result_data['error']}")
                    return False, result_data['error']
            else:
                return False, "No output from subprocess"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Subprocess timeout after {timeout_seconds}s")
            process.kill()
            return False, f"Timeout after {timeout_seconds}s"
            
        except Exception as e:
            logger.error(f"Error in subprocess handler: {e}")
            if 'process' in locals():
                try:
                    process.kill()
                except:
                    pass
            return False, str(e)
            
        finally:
            # Cleanup temp files
            for path in [input_path, output_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except:
                    pass
    
    def _check_resource_limits(self) -> bool:
        """Check if we're within CPU and memory limits."""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)
            if cpu_percent > self.max_cpu_percent:
                logger.warning(f"CPU usage {cpu_percent}% exceeds limit {self.max_cpu_percent}%")
                return False
            
            # Check memory usage
            memory = psutil.virtual_memory()
            memory_percent_used = memory.percent
            if memory_percent_used > (100 - self.max_memory_percent):
                logger.warning(
                    f"Memory usage {memory_percent_used}% exceeds limit "
                    f"(available: {self.max_memory_percent}%)"
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking resource limits: {e}")
            return True  # Continue on error


class HybridTimeoutHandler:
    """
    Hybrid approach using threading for orchestration and subprocess for heavy operations.
    Best of both worlds: low overhead + reliable termination.
    """
    
    def __init__(self, max_cpu_percent=50, max_memory_percent=50):
        self.subprocess_handler = SubprocessTimeoutHandler(max_cpu_percent, max_memory_percent)
        
    def should_use_subprocess(self, file_path: str) -> bool:
        """
        Determine if we should use subprocess (for large/problematic files)
        or can use threading (for small files).
        """
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Use subprocess for:
            # - Large files (>10MB) - higher risk of hanging
            # - PDFs (known to have extraction issues)
            # - EPUBs (file descriptor issues)
            # - Any previously failed files
            
            if file_size_mb > 10:
                return True
                
            ext = Path(file_path).suffix.lower()
            if ext in ['.pdf', '.epub', '.mobi', '.azw', '.azw3']:
                return True
                
            return False
            
        except:
            # If in doubt, use subprocess for safety
            return True
    
    def process_document(
        self,
        file_path: str,
        processor_func: Callable,
        timeout_seconds: int,
        progress_file: Optional[str] = None
    ) -> tuple[bool, Any]:
        """
        Process a document with appropriate timeout mechanism.
        """
        if self.should_use_subprocess(file_path):
            # Use subprocess for reliable termination
            logger.info(f"Using subprocess for {Path(file_path).name}")
            return self.subprocess_handler.process_with_timeout(
                processor_func.__module__,
                processor_func.__name__,
                (file_path,),
                timeout_seconds,
                progress_file
            )
        else:
            # Use threading for small files (lower overhead)
            logger.info(f"Using threading for {Path(file_path).name}")
            # Existing threading implementation
            # (kept for backwards compatibility with small files)
            from concurrent.futures import ThreadPoolExecutor, TimeoutError
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(processor_func, file_path)
                try:
                    result = future.result(timeout=timeout_seconds)
                    return True, result
                except TimeoutError:
                    return False, f"Timeout after {timeout_seconds}s"
                except Exception as e:
                    return False, str(e)