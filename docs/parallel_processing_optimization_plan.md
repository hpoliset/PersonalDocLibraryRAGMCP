# Parallel Processing Optimization Plan

## Current State Analysis

### System Specs
- **CPU Cores**: 14 physical cores (ARM64 M-series Mac)
- **Current Usage**: ~37% CPU (19.88% user + 17.57% sys)
- **Available Capacity**: ~63% idle
- **Memory**: 1GB+ used by indexer, plenty available

### Current Implementation Issues
1. **Static Worker Limit**: Max 5 workers regardless of system capacity
2. **No Dynamic Scaling**: Fixed worker count throughout processing
3. **Large File Bottleneck**: Sequential processing for files >50MB causes delays
4. **Resource Underutilization**: Only using ~35% of CPU capacity
5. **No Load-Based Adjustment**: Doesn't adapt to system conditions

## Proposed Optimization Strategy

### 1. Dynamic Thread Ramping System

#### Phase 1: Smart Initial Worker Calculation
```python
def calculate_initial_workers(self):
    cpu_count = multiprocessing.cpu_count()
    available_memory_gb = psutil.virtual_memory().available / (1024**3)
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Base calculation: 70% of cores for heavy processing
    base_workers = int(cpu_count * 0.7)
    
    # Adjust based on CPU load
    if cpu_percent < 30:
        # Low load: can use more workers
        workers = min(base_workers, cpu_count - 2)
    elif cpu_percent < 60:
        # Medium load: moderate workers
        workers = min(base_workers, cpu_count // 2)
    else:
        # High load: conservative
        workers = max(2, cpu_count // 4)
    
    # Memory constraint (500MB per worker estimate)
    memory_limited_workers = int(available_memory_gb * 2)
    
    return min(workers, memory_limited_workers, 12)  # Cap at 12
```

#### Phase 2: Adaptive Scaling During Processing
```python
class AdaptiveThreadManager:
    def __init__(self):
        self.min_workers = 2
        self.max_workers = 12
        self.current_workers = 4
        self.performance_history = []
        self.scale_interval = 60  # seconds
        
    def should_scale_up(self):
        # Scale up if:
        # - CPU usage < 50% 
        # - Memory available > 2GB
        # - Queue has > 10 pending items
        # - Processing rate is stable
        
    def should_scale_down(self):
        # Scale down if:
        # - CPU usage > 80%
        # - Memory pressure detected
        # - Error rate increasing
        # - File descriptor usage > 80%
```

### 2. Tiered Processing Pools

#### Document Classification
```python
class DocumentClassifier:
    TINY = (0, 1)           # < 1MB: Quick processing
    SMALL = (1, 10)         # 1-10MB: Standard processing  
    MEDIUM = (10, 50)       # 10-50MB: Careful processing
    LARGE = (50, 200)       # 50-200MB: Sequential with progress
    HUGE = (200, float('inf'))  # >200MB: Special handling
```

#### Pool Configuration
1. **Fast Pool** (8 workers): TINY & SMALL files
2. **Standard Pool** (4 workers): MEDIUM files  
3. **Heavy Pool** (2 workers): LARGE files
4. **Sequential Pool** (1 worker): HUGE files with adaptive timeout

### 3. Resource Monitoring & Protection

#### CPU Governor
```python
class CPUGovernor:
    def __init__(self):
        self.target_cpu_percent = 70
        self.critical_cpu_percent = 85
        self.check_interval = 10
        
    def adjust_workers(self, executor):
        current_cpu = psutil.cpu_percent(interval=1)
        
        if current_cpu > self.critical_cpu_percent:
            # Emergency throttle
            executor.reduce_workers(2)
        elif current_cpu > self.target_cpu_percent:
            # Gradual reduction
            executor.reduce_workers(1)
        elif current_cpu < self.target_cpu_percent - 20:
            # Room to grow
            executor.add_workers(1)
```

#### Memory Monitor
```python
class MemoryMonitor:
    def __init__(self):
        self.min_free_gb = 1.5
        self.worker_memory_estimate_mb = 500
        
    def get_safe_worker_count(self):
        available_gb = psutil.virtual_memory().available / (1024**3)
        return int((available_gb - self.min_free_gb) * 1024 / 
                   self.worker_memory_estimate_mb)
```

### 4. Smart Queue Management

#### Priority Queue System
```python
class SmartQueue:
    def __init__(self):
        self.queues = {
            'retry': [],      # Failed items for retry
            'small': [],      # Quick wins
            'medium': [],     # Standard processing
            'large': [],      # Heavy processing
        }
        
    def get_next_batch(self, worker_count):
        # Distribute work based on worker availability
        # Mix of sizes to maximize throughput
        batch = []
        
        # 60% small files for quick completions
        small_count = int(worker_count * 0.6)
        batch.extend(self.queues['small'][:small_count])
        
        # 30% medium files
        medium_count = int(worker_count * 0.3)
        batch.extend(self.queues['medium'][:medium_count])
        
        # 10% large files (if workers available)
        if worker_count > 8:
            batch.extend(self.queues['large'][:1])
            
        return batch
```

### 5. Implementation Phases

#### Phase 1: Foundation (Week 1)
- [ ] Implement DocumentClassifier
- [ ] Create CPUGovernor and MemoryMonitor
- [ ] Add performance metrics collection
- [ ] Test with synthetic workload

#### Phase 2: Dynamic Scaling (Week 2)
- [ ] Implement AdaptiveThreadManager
- [ ] Add scale up/down logic
- [ ] Create resource protection mechanisms
- [ ] Test with real document set

#### Phase 3: Advanced Features (Week 3)
- [ ] Implement tiered processing pools
- [ ] Add smart queue management
- [ ] Create predictive scaling based on document analysis
- [ ] Performance tuning and optimization

### 6. Performance Targets

#### Current Performance
- **Processing Rate**: ~540 pages/minute (single large PDF)
- **Worker Count**: Max 5 workers
- **CPU Utilization**: ~37%
- **Throughput**: 1 document at a time for large files

#### Target Performance
- **Processing Rate**: 1500+ pages/minute (with parallel extraction)
- **Worker Count**: Dynamic 2-12 based on load
- **CPU Utilization**: 60-75% (optimal range)
- **Throughput**: 8-12 documents in parallel

### 7. Special Handling for Edge Cases

#### Massive Documents (>500MB or >10K pages)
```python
class MassiveDocumentHandler:
    def process(self, filepath):
        # 1. Split PDF into chunks
        # 2. Process chunks in parallel
        # 3. Merge results
        # 4. Clean up temp files
```

#### EPUB File Descriptor Management
```python
class EPUBProcessor:
    def __init__(self):
        self.max_concurrent_epubs = 2
        self.epub_semaphore = Semaphore(2)
        
    def process_with_fd_protection(self, filepath):
        with self.epub_semaphore:
            # Process EPUB with limited concurrency
            # Force garbage collection after processing
```

### 8. Monitoring & Metrics

#### Key Metrics to Track
- Documents per minute
- Pages per minute  
- Average processing time by document size
- Worker efficiency (docs processed / worker)
- Error rate by document type
- Resource utilization over time

#### Dashboard Updates
```python
monitoring_stats = {
    "workers": {
        "active": current_workers,
        "idle": idle_workers,
        "efficiency": docs_per_worker
    },
    "performance": {
        "docs_per_min": current_rate,
        "pages_per_min": page_rate,
        "queue_depth": pending_count
    },
    "resources": {
        "cpu_percent": cpu_usage,
        "memory_gb": memory_used,
        "fd_usage": fd_percent
    }
}
```

## Implementation Priority

1. **Immediate** (After current indexing completes):
   - Increase base worker limit from 5 to 8
   - Add CPU monitoring to prevent overload
   - Implement document size classification

2. **Short-term** (Next iteration):
   - Dynamic worker scaling
   - Tiered processing pools
   - Memory-based constraints

3. **Long-term** (Future enhancement):
   - Predictive scaling
   - Distributed processing support
   - ML-based optimization

## Risk Mitigation

1. **Gradual Rollout**: Test with small batches first
2. **Fallback Mode**: Revert to conservative settings if issues detected
3. **Resource Limits**: Hard caps on workers and memory usage
4. **Monitoring**: Comprehensive logging and alerting
5. **Testing**: Thorough testing with various document types and sizes

## Expected Benefits

- **3-5x faster** processing for mixed document libraries
- **Better resource utilization** (60-75% vs current 35%)
- **Reduced failure rate** through appropriate timeout/worker allocation
- **Improved responsiveness** for small documents
- **Scalability** for large document collections

This plan provides a roadmap for optimizing parallel processing while preventing CPU overload through intelligent monitoring and adaptive scaling.