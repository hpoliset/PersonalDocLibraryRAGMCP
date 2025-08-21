# Timeout and Process Management Fix
# This file contains the fixed implementation for document processing with proper timeout handling

import os
import time
import json
import signal
import psutil
import threading
import multiprocessing
from multiprocessing import Process, Queue, Value
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DocumentProcessorWithTimeout:
    """
    Fixed document processor that:
    1. Uses Process instead of Thread for killable operations
    2. Extends timeout as long as progress is seen every 5 minutes
    3. Properly terminates processes to prevent zombies
    4. Enforces CPU and memory limits (50% max)
    """
    
    def __init__(self, db_directory, max_cpu_percent=50, max_memory_percent=50):
        self.db_directory = db_directory
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.progress_file = os.path.join(db_directory, "indexing_progress.json")
        
    def process_document_with_timeout(self, filepath, rel_path, loader_func):
        """
        Process a document with proper timeout and process management.
        
        Args:
            filepath: Path to the document
            rel_path: Relative path for logging
            loader_func: Function to load/process the document
            
        Returns:
            Loaded documents or False on failure
        """
        # Get file size for timeout calculation
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        # Calculate initial timeout based on file size
        timeout_seconds = self._calculate_initial_timeout(file_size_mb)
        
        # Calculate extension time based on file size
        extension_time = self._calculate_extension_time(file_size_mb)
        
        logger.info(f"Processing {rel_path} ({file_size_mb:.1f}MB) with initial timeout {timeout_seconds}s")
        
        # Create queues for communication
        result_queue = Queue()
        exception_queue = Queue()
        progress_value = Value('i', 0)
        
        # Create the process
        process = Process(
            target=self._load_document_in_process,
            args=(filepath, loader_func, result_queue, exception_queue, progress_value, self.progress_file)
        )
        
        # Start the process
        process.start()
        
        # Monitor the process with adaptive timeout
        start_time = time.time()
        last_progress_time = start_time
        last_progress_value = 0
        extensions_granted = 0
        no_progress_window = 300  # 5 minutes without progress = kill
        
        while process.is_alive():
            elapsed = time.time() - start_time
            time_since_progress = time.time() - last_progress_time
            
            # Check system resources
            if not self._check_resource_limits():
                logger.warning("Resource limits exceeded, terminating process")
                self._terminate_process(process)
                return False
            
            # Sleep for a short interval
            time.sleep(2)
            
            # Check progress
            current_progress = self._read_progress(progress_value, self.progress_file)
            
            if current_progress != last_progress_value:
                # Progress detected
                progress_delta = current_progress - last_progress_value
                logger.info(f"Progress: {current_progress} (+{progress_delta}) for {rel_path}")
                last_progress_value = current_progress
                last_progress_time = time.time()
                
            # Check if we should extend or timeout
            if elapsed > timeout_seconds:
                # Check if progress was made within the no_progress_window
                if time_since_progress < no_progress_window:
                    # Recent progress detected, extend timeout
                    extensions_granted += 1
                    timeout_seconds += extension_time
                    logger.info(
                        f"Extension #{extensions_granted} granted: +{extension_time/60:.0f} min "
                        f"(total: {timeout_seconds/60:.0f} min) for {rel_path}"
                    )
                else:
                    # No recent progress, terminate
                    logger.error(
                        f"No progress for {time_since_progress/60:.1f} minutes, "
                        f"terminating after {elapsed/60:.1f} minutes: {rel_path}"
                    )
                    self._terminate_process(process)
                    return False
            
            # Also check for stalled process (no progress for 5 minutes)
            if time_since_progress > no_progress_window:
                logger.error(
                    f"Process stalled (no progress for {no_progress_window/60:.0f} min), "
                    f"terminating: {rel_path}"
                )
                self._terminate_process(process)
                return False
        
        # Process finished, get results
        process.join(timeout=5)
        
        # Check for exceptions
        if not exception_queue.empty():
            error = exception_queue.get()
            logger.error(f"Error processing {rel_path}: {error}")
            return False
        
        # Get results
        if not result_queue.empty():
            docs = result_queue.get()
            logger.info(f"Successfully processed {rel_path} in {(time.time()-start_time)/60:.1f} minutes")
            return docs
        
        return False
    
    def _load_document_in_process(self, filepath, loader_func, result_queue, exception_queue, progress_value, progress_file):
        """
        Load document in a separate process (can be killed).
        """
        try:
            # Set up progress tracking
            def update_progress(current_page=None, total_pages=None, chunks=None):
                if current_page is not None:
                    progress_value.value = current_page
                    # Write to progress file
                    try:
                        progress_data = {
                            "timestamp": datetime.now().isoformat(),
                            "stage": "extracting",
                            "current_page": current_page,
                            "total_pages": total_pages,
                            "chunks_generated": chunks,
                            "memory_mb": psutil.Process().memory_info().rss / (1024 * 1024),
                            "current_file": os.path.basename(filepath)
                        }
                        with open(progress_file, 'w') as f:
                            json.dump(progress_data, f)
                    except:
                        pass  # Ignore errors writing progress
            
            # Load the document with progress callback
            docs = loader_func(filepath, progress_callback=update_progress)
            result_queue.put(docs)
            
        except Exception as e:
            exception_queue.put(e)
    
    def _terminate_process(self, process):
        """
        Properly terminate a process and all its children.
        """
        try:
            # First try to terminate gracefully
            process.terminate()
            process.join(timeout=5)
            
            if process.is_alive():
                # Force kill if still alive
                logger.warning("Process didn't terminate gracefully, force killing")
                process.kill()
                process.join(timeout=5)
                
            # Clean up any zombie children
            try:
                parent = psutil.Process(process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.kill()
                    except:
                        pass
            except:
                pass  # Process might already be gone
                
        except Exception as e:
            logger.error(f"Error terminating process: {e}")
    
    def _calculate_initial_timeout(self, file_size_mb):
        """
        Calculate initial timeout based on file size.
        """
        if file_size_mb < 10:
            return 300  # 5 minutes
        elif file_size_mb < 50:
            return 600  # 10 minutes
        elif file_size_mb < 100:
            return 900  # 15 minutes
        elif file_size_mb < 300:
            return 1200  # 20 minutes
        else:
            return 1800  # 30 minutes
    
    def _calculate_extension_time(self, file_size_mb):
        """
        Calculate extension time based on file size.
        """
        if file_size_mb < 10:
            return 300  # 5 minutes
        elif file_size_mb < 50:
            return 600  # 10 minutes
        elif file_size_mb < 200:
            return 900  # 15 minutes
        else:
            return 1200  # 20 minutes
    
    def _read_progress(self, progress_value, progress_file):
        """
        Read progress from shared value or file.
        """
        # First try shared value
        if progress_value.value > 0:
            return progress_value.value
            
        # Then try file
        try:
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    return data.get('current_page', 0) or data.get('chunks_generated', 0)
        except:
            pass
            
        return 0
    
    def _check_resource_limits(self):
        """
        Check if we're within CPU and memory limits.
        """
        try:
            # Check CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.max_cpu_percent:
                logger.warning(f"CPU usage {cpu_percent}% exceeds limit {self.max_cpu_percent}%")
                return False
            
            # Check memory usage
            memory = psutil.virtual_memory()
            memory_percent_used = 100 - memory.percent  # percent of available memory
            if memory_percent_used > self.max_memory_percent:
                logger.warning(f"Memory usage {memory_percent_used}% exceeds limit {self.max_memory_percent}%")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking resource limits: {e}")
            return True  # Continue on error


class AdaptiveWorkerManager:
    """
    Hardware-agnostic worker manager that adapts to any system.
    Ensures we never exceed 50% CPU or 50% available memory.
    Dynamically detects and adapts to system specifications.
    """
    
    def __init__(self, max_cpu_percent=50, max_memory_percent=50):
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        
        # Dynamically detect hardware
        self.cpu_count = multiprocessing.cpu_count()
        self.total_memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Calculate limits based on actual hardware
        self.min_workers = 1
        # Max workers is 50% of CPU cores (to stay under 50% CPU usage)
        self.max_workers = max(1, self.cpu_count // 2)
        
        # Adjust for memory constraints (500MB per worker estimate)
        memory_based_max = int((self.total_memory_gb * 0.5) / 0.5)
        self.max_workers = min(self.max_workers, memory_based_max)
        
        logger.info(
            f"AdaptiveWorkerManager initialized: "
            f"CPUs={self.cpu_count}, Memory={self.total_memory_gb:.1f}GB, "
            f"MaxWorkers={self.max_workers}"
        )
        
    def calculate_optimal_workers(self):
        """
        Calculate optimal number of workers based on current system state.
        """
        try:
            # Get current CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get available memory
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            
            # Calculate CPU-based limit
            # If CPU is at 20%, we can use up to 30% more (to reach 50%)
            cpu_headroom = self.max_cpu_percent - cpu_percent
            cpu_based_workers = max(1, int(cpu_headroom / 10))  # ~10% per worker
            
            # Calculate memory-based limit (assume 500MB per worker)
            # Only use half of available memory
            memory_based_workers = int((available_memory_gb * 0.5) / 0.5)  # 500MB per worker
            
            # Take the minimum to be safe
            optimal_workers = min(
                cpu_based_workers,
                memory_based_workers,
                self.max_workers
            )
            
            # Ensure at least min_workers
            optimal_workers = max(self.min_workers, optimal_workers)
            
            logger.info(
                f"Worker calculation: CPU={cpu_percent:.1f}% (headroom for {cpu_based_workers}), "
                f"Memory={available_memory_gb:.1f}GB (supports {memory_based_workers}), "
                f"Optimal={optimal_workers}"
            )
            
            return optimal_workers
            
        except Exception as e:
            logger.error(f"Error calculating workers: {e}")
            return self.min_workers
    
    def should_scale_up(self, current_workers, queue_size):
        """
        Determine if we should add more workers.
        """
        if queue_size < 5:
            return False  # Not enough work
            
        if current_workers >= self.max_workers:
            return False  # Already at max
            
        cpu_percent = psutil.cpu_percent(interval=0.5)
        if cpu_percent > self.max_cpu_percent - 10:
            return False  # Too close to CPU limit
            
        memory = psutil.virtual_memory()
        if memory.percent > 100 - self.max_memory_percent:
            return False  # Too close to memory limit
            
        return True
    
    def should_scale_down(self, current_workers):
        """
        Determine if we should reduce workers.
        """
        if current_workers <= self.min_workers:
            return False  # Already at minimum
            
        cpu_percent = psutil.cpu_percent(interval=0.5)
        if cpu_percent > self.max_cpu_percent:
            return True  # Over CPU limit
            
        memory = psutil.virtual_memory()
        if memory.percent > 100 - self.max_memory_percent + 10:
            return True  # Over memory limit
            
        return False


# Integration patch for shared_rag.py
def create_timeout_patch():
    """
    Returns the patch to apply to shared_rag.py to fix the timeout issues.
    """
    patch = '''
# Replace the existing process_document_with_timeout method with:

def process_document_with_timeout(self, filepath, rel_path):
    """Process document with proper timeout and zombie prevention."""
    processor = DocumentProcessorWithTimeout(
        self.db_directory,
        max_cpu_percent=50,
        max_memory_percent=50
    )
    
    # Create a loader function that works with the processor
    def loader_func(filepath, progress_callback=None):
        loader = self.get_document_loader(filepath)
        # Hook into loader's progress if available
        if hasattr(loader, 'set_progress_callback'):
            loader.set_progress_callback(progress_callback)
        return loader.load()
    
    return processor.process_document_with_timeout(filepath, rel_path, loader_func)
'''
    return patch