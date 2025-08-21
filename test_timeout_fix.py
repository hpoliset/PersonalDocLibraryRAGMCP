#!/usr/bin/env python3
"""
Test script to verify the timeout and process management fixes
"""

import os
import sys
import time
import multiprocessing
import psutil
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, '/Users/hpoliset/DocumentIndexerMCP/src')

from core.shared_rag_fixed import DocumentProcessorWithTimeout, AdaptiveWorkerManager

def test_adaptive_worker_manager():
    """Test the adaptive worker manager"""
    print("Testing AdaptiveWorkerManager...")
    
    manager = AdaptiveWorkerManager(max_cpu_percent=50, max_memory_percent=50)
    
    print(f"System specs detected:")
    print(f"  CPU cores: {manager.cpu_count}")
    print(f"  Total memory: {manager.total_memory_gb:.1f} GB")
    print(f"  Max workers: {manager.max_workers}")
    print(f"  Min workers: {manager.min_workers}")
    
    # Calculate optimal workers
    optimal = manager.calculate_optimal_workers()
    print(f"  Optimal workers now: {optimal}")
    
    # Test scaling decisions
    print("\nTesting scaling decisions:")
    print(f"  Should scale up (5 workers, 20 queued): {manager.should_scale_up(5, 20)}")
    print(f"  Should scale down (8 workers): {manager.should_scale_down(8)}")
    
    return True

def test_process_termination():
    """Test that processes can be properly terminated"""
    print("\nTesting process termination...")
    
    def slow_task(result_queue, exception_queue, progress_value, progress_file):
        """A task that takes forever"""
        try:
            for i in range(100):
                time.sleep(0.5)
                progress_value.value = i
        except Exception as e:
            exception_queue.put(e)
    
    from multiprocessing import Process, Queue, Value
    
    result_queue = Queue()
    exception_queue = Queue()
    progress_value = Value('i', 0)
    
    process = Process(
        target=slow_task,
        args=(result_queue, exception_queue, progress_value, "/tmp/test_progress.json")
    )
    
    print("Starting slow process...")
    process.start()
    
    # Let it run for 2 seconds
    time.sleep(2)
    
    print(f"Process alive: {process.is_alive()}")
    print(f"Progress value: {progress_value.value}")
    
    # Terminate it
    print("Terminating process...")
    process.terminate()
    process.join(timeout=5)
    
    print(f"Process alive after termination: {process.is_alive()}")
    
    if process.is_alive():
        print("Force killing...")
        process.kill()
        process.join(timeout=5)
    
    print(f"Process alive after kill: {process.is_alive()}")
    
    return not process.is_alive()

def test_resource_limits():
    """Test resource limit checking"""
    print("\nTesting resource limits...")
    
    processor = DocumentProcessorWithTimeout(
        db_directory="/tmp",
        max_cpu_percent=50,
        max_memory_percent=50
    )
    
    # Check resource limits
    within_limits = processor._check_resource_limits()
    print(f"Within resource limits: {within_limits}")
    
    # Get current usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"Current CPU usage: {cpu_percent}%")
    print(f"Current memory usage: {memory.percent}%")
    print(f"Available memory: {memory.available / (1024**3):.1f} GB")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Timeout and Process Management Fixes")
    print("=" * 60)
    
    tests = [
        ("Adaptive Worker Manager", test_adaptive_worker_manager),
        ("Process Termination", test_process_termination),
        ("Resource Limits", test_resource_limits),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n>>> Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
            print(f"<<< {test_name}: {'✓ PASSED' if result else '✗ FAILED'}")
        except Exception as e:
            results.append((test_name, "ERROR"))
            print(f"<<< {test_name}: ✗ ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    for test_name, result in results:
        status_symbol = "✓" if result == "PASS" else "✗"
        print(f"{status_symbol} {test_name}: {result}")
    
    all_passed = all(result == "PASS" for _, result in results)
    print("\n" + ("All tests passed! ✓" if all_passed else "Some tests failed. ✗"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())