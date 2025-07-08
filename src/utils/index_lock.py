#!/usr/bin/env python3
"""
File-based locking system for preventing concurrent indexing operations
"""

import os
import fcntl
import time
import signal
import logging

logger = logging.getLogger(__name__)

class IndexLock:
    """File-based locking to prevent simultaneous indexing with stale lock detection"""
    def __init__(self, lock_file="/tmp/spiritual_library_index.lock", stale_timeout_minutes=30):
        self.lock_file = lock_file
        self.lock_fd = None
        self.stale_timeout_minutes = stale_timeout_minutes
        # Clean stale locks on initialization
        self.clean_stale_lock()
    
    def is_lock_stale(self):
        """Check if existing lock file is from a dead process or too old"""
        if not os.path.exists(self.lock_file):
            return False
        
        try:
            # Check file age
            mtime = os.path.getmtime(self.lock_file)
            age_minutes = (time.time() - mtime) / 60
            
            if age_minutes > self.stale_timeout_minutes:
                logger.info(f"Lock file is {age_minutes:.1f} minutes old, considering stale")
                return True
            
            # Try to read PID from lock file
            with open(self.lock_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    try:
                        pid = int(lines[0].strip())
                        # Check if process is still alive
                        os.kill(pid, 0)
                        return False  # Process exists
                    except (ValueError, ProcessLookupError):
                        logger.info(f"Lock file PID {lines[0].strip()} is not running, considering stale")
                        return True
                    except PermissionError:
                        # Process exists but we can't signal it
                        return False
        except Exception as e:
            logger.error(f"Error checking lock staleness: {e}")
            return True  # Consider stale if we can't check
        
        return False
    
    def clean_stale_lock(self):
        """Remove stale lock file if detected"""
        if self.is_lock_stale():
            try:
                os.remove(self.lock_file)
                logger.info(f"Removed stale lock file: {self.lock_file}")
            except Exception as e:
                logger.error(f"Error removing stale lock: {e}")
    
    def acquire(self, blocking=True, timeout=None):
        """Context manager for acquiring lock"""
        return self._LockContext(self, blocking, timeout)
    
    def get_lock_info(self):
        """Get information about current lock status"""
        info = {
            'exists': os.path.exists(self.lock_file),
            'stale': False,
            'pid': None,
            'age_minutes': 0
        }
        
        if info['exists']:
            info['stale'] = self.is_lock_stale()
            
            try:
                mtime = os.path.getmtime(self.lock_file)
                info['age_minutes'] = (time.time() - mtime) / 60
                
                with open(self.lock_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        info['pid'] = int(lines[0].strip())
            except:
                pass
        
        return info
    
    class _LockContext:
        def __init__(self, lock_instance, blocking=True, timeout=None):
            self.lock_instance = lock_instance
            self.blocking = blocking
            self.timeout = timeout
            self.lock_fd = None
            
        def __enter__(self):
            # Clean stale locks before trying to acquire
            self.lock_instance.clean_stale_lock()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.lock_instance.lock_file), exist_ok=True)
            
            # Open or create the lock file
            self.lock_fd = open(self.lock_instance.lock_file, 'a')
            
            # Try to acquire exclusive lock
            flags = fcntl.LOCK_EX
            if not self.blocking:
                flags |= fcntl.LOCK_NB
                
            if self.timeout:
                # Implement timeout using alarm signal
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Could not acquire lock within {self.timeout} seconds")
                
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout)
            
            try:
                fcntl.flock(self.lock_fd.fileno(), flags)
                
                # Write our PID to the lock file
                self.lock_fd.seek(0)
                self.lock_fd.truncate()
                self.lock_fd.write(f"{os.getpid()}\n")
                self.lock_fd.write(f"{time.time()}\n")
                self.lock_fd.flush()
                
                logger.info(f"Acquired lock: {self.lock_instance.lock_file}")
                
            except IOError as e:
                if e.errno in (11, 35):  # EAGAIN or EWOULDBLOCK
                    self.lock_fd.close()
                    raise IOError("Could not acquire lock - another process is indexing")
                raise
            finally:
                if self.timeout:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                    
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.lock_fd:
                try:
                    # Release the lock
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                    self.lock_fd.close()
                    
                    # Remove the lock file
                    try:
                        os.remove(self.lock_instance.lock_file)
                        logger.info(f"Released and removed lock: {self.lock_instance.lock_file}")
                    except:
                        pass
                except:
                    pass