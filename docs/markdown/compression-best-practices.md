# Compression Best Practices

This guide provides recommendations for effectively using automatic compression in Valkey GLIDE to optimize performance, reduce bandwidth usage, and maintain application reliability.

## When to Use Compression

### ✅ Ideal Use Cases

**Large JSON Payloads**
```python
# Excellent compression candidate
user_profile = {
    "user_id": "12345",
    "preferences": {...},
    "activity_history": [...],  # Large arrays
    "metadata": {...}
}
# JSON with repetitive structure compresses very well
```

**Text Data with Repetitive Content**
```python
# High compression ratio expected
log_data = "2024-01-01 10:00:00 INFO Application started\n" * 1000
template_content = "<div class='item'>...</div>" * 500
```

**Serialized Objects**
```python
# Good compression for structured data
import pickle
serialized_data = pickle.dumps(large_object_list)
```

**High-Bandwidth Applications**
- Applications with frequent large data transfers
- Microservices with heavy inter-service communication
- Mobile applications with limited bandwidth

**Storage-Constrained Environments**
- Redis instances with memory limitations
- Cost-sensitive cloud deployments
- Applications with long-term data retention

### ❌ Poor Use Cases

**Small Values (< 64 bytes)**
```python
# Don't compress - overhead exceeds benefit
small_values = {
    "user:123:status": "active",
    "counter": "42",
    "flag": "true"
}
```

**Already Compressed Data**
```python
# Minimal or negative compression benefit
import gzip
compressed_image = gzip.compress(image_data)
video_file = open("video.mp4", "rb").read()  # Already compressed
```

**High-Frequency, Low-Latency Operations**
```python
# Compression adds latency to critical path
session_tokens = "abc123def456"  # Frequent access, small size
real_time_metrics = {"cpu": 45.2, "memory": 78.1}  # Latency-sensitive
```

**Binary Data with High Entropy**
```python
# Random data doesn't compress well
encryption_keys = os.urandom(256)
random_data = secrets.token_bytes(1024)
```

## Configuration Recommendations

### Development Environment

**Fast Iteration Configuration**
```python
development_config = CompressionConfiguration(
    enabled=True,
    compression_level=1,  # Fastest compression
    min_compression_size=32,  # Lower threshold for testing
    max_compression_size=1024*1024  # 1MB limit for safety
)
```

**Benefits:**
- Fast compression for quick development cycles
- Lower threshold to test compression behavior
- Size limit prevents accidental large value compression

### Production Environments

**High-Throughput Applications**
```python
high_throughput_config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=1,  # Prioritize speed
    min_compression_size=128,  # Skip small values
    max_compression_size=5*1024*1024  # 5MB limit
)
```

**Storage-Optimized Applications**
```python
storage_optimized_config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=6,  # Better compression ratio
    min_compression_size=64,  # Standard threshold
    max_compression_size=50*1024*1024  # 50MB limit
)
```

**Balanced Production Configuration (Recommended)**
```python
balanced_config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=3,  # Good balance
    min_compression_size=64,  # Skip small values
    max_compression_size=10*1024*1024  # 10MB limit
)
```

### Microservices Architecture

**Service-to-Service Communication**
```python
# For internal service communication
internal_service_config = CompressionConfiguration(
    enabled=True,
    compression_level=2,  # Fast for internal networks
    min_compression_size=256,  # Higher threshold for internal use
    max_compression_size=2*1024*1024  # 2MB limit
)
```

**External API Responses**
```python
# For external-facing services
external_api_config = CompressionConfiguration(
    enabled=True,
    compression_level=4,  # Better compression for external bandwidth
    min_compression_size=128,
    max_compression_size=5*1024*1024  # 5MB limit
)
```

## Performance Optimization

### Compression Level Guidelines

| Level | Use Case | Compression Speed | Compression Ratio | CPU Usage |
|-------|----------|-------------------|-------------------|-----------|
| 1 | High-frequency operations | Fastest | Good | Low |
| 3 | Balanced production | Fast | Better | Medium |
| 6 | Storage optimization | Medium | Best | High |
| 9+ | Archival/batch processing | Slow | Excellent | Very High |

### Size Threshold Optimization

**Analyze Your Data Distribution**
```python
import asyncio
from collections import defaultdict

async def analyze_value_sizes(client, sample_keys):
    """Analyze value size distribution to optimize thresholds."""
    size_distribution = defaultdict(int)
    
    for key in sample_keys:
        value = await client.get(key)
        if value:
            size = len(value.encode() if isinstance(value, str) else value)
            # Bucket sizes
            if size < 32:
                size_distribution['< 32 bytes'] += 1
            elif size < 64:
                size_distribution['32-64 bytes'] += 1
            elif size < 128:
                size_distribution['64-128 bytes'] += 1
            elif size < 512:
                size_distribution['128-512 bytes'] += 1
            elif size < 1024:
                size_distribution['512B-1KB'] += 1
            else:
                size_distribution['> 1KB'] += 1
    
    return size_distribution

# Use results to set optimal min_compression_size
```

**Recommended Thresholds by Use Case**

| Use Case | Min Size | Reasoning |
|----------|----------|-----------|
| General purpose | 64 bytes | Good balance, avoids small value overhead |
| High-performance | 128-256 bytes | Reduces compression overhead |
| Storage-optimized | 32 bytes | Maximizes compression opportunities |
| Bandwidth-constrained | 32 bytes | Every byte saved matters |

### Memory Usage Optimization

**Monitor Memory Impact**
```python
import psutil
import asyncio

async def monitor_compression_memory():
    """Monitor memory usage with compression enabled."""
    process = psutil.Process()
    
    # Baseline memory
    baseline_memory = process.memory_info().rss
    
    # Perform operations with compression
    # ... your operations here ...
    
    # Check memory after operations
    current_memory = process.memory_info().rss
    memory_increase = current_memory - baseline_memory
    
    print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
    return memory_increase
```

**Memory-Conscious Configuration**
```python
memory_conscious_config = CompressionConfiguration(
    enabled=True,
    compression_level=2,  # Lower CPU and memory usage
    min_compression_size=256,  # Higher threshold
    max_compression_size=1024*1024  # Limit max memory per operation
)
```

## Application Integration Patterns

### Gradual Rollout Pattern

**Phase 1: Canary Deployment**
```python
import os

def get_compression_config():
    """Feature flag controlled compression."""
    if os.getenv('COMPRESSION_CANARY', 'false').lower() == 'true':
        return CompressionConfiguration(
            enabled=True,
            compression_level=1,  # Conservative settings
            min_compression_size=128
        )
    return CompressionConfiguration(enabled=False)
```

**Phase 2: Percentage Rollout**
```python
import random

def get_compression_config(user_id):
    """Percentage-based rollout."""
    rollout_percentage = int(os.getenv('COMPRESSION_ROLLOUT_PERCENT', '0'))
    user_hash = hash(user_id) % 100
    
    if user_hash < rollout_percentage:
        return CompressionConfiguration(enabled=True)
    return CompressionConfiguration(enabled=False)
```

### Configuration Management Pattern

**Centralized Configuration**
```python
class CompressionConfigManager:
    def __init__(self):
        self.configs = {
            'development': CompressionConfiguration(
                enabled=True,
                compression_level=1,
                min_compression_size=32
            ),
            'staging': CompressionConfiguration(
                enabled=True,
                compression_level=3,
                min_compression_size=64
            ),
            'production': CompressionConfiguration(
                enabled=True,
                compression_level=3,
                min_compression_size=64,
                max_compression_size=10*1024*1024
            )
        }
    
    def get_config(self, environment):
        return self.configs.get(environment, self.configs['production'])
```

### Error Handling Pattern

**Graceful Degradation**
```python
class ResilientCompressionClient:
    def __init__(self, primary_config, fallback_config):
        self.primary_config = primary_config
        self.fallback_config = fallback_config
        self.client = None
        self.fallback_client = None
    
    async def get_client(self):
        if self.client is None:
            try:
                self.client = await GlideClient.create(
                    GlideClientConfiguration(
                        addresses=[...],
                        compression=self.primary_config
                    )
                )
            except Exception as e:
                logger.warning(f"Primary compression config failed: {e}")
                self.client = await GlideClient.create(
                    GlideClientConfiguration(
                        addresses=[...],
                        compression=self.fallback_config
                    )
                )
        return self.client
```

## Monitoring and Observability

### Key Metrics to Track

**Compression Effectiveness**
```python
class CompressionMetrics:
    def __init__(self):
        self.operations = 0
        self.bytes_before = 0
        self.bytes_after = 0
        self.compression_time = 0
        self.decompression_time = 0
        self.errors = 0
    
    def record_compression(self, original_size, compressed_size, duration):
        self.operations += 1
        self.bytes_before += original_size
        self.bytes_after += compressed_size
        self.compression_time += duration
    
    def get_compression_ratio(self):
        if self.bytes_before == 0:
            return 0
        return self.bytes_after / self.bytes_before
    
    def get_space_saved(self):
        return self.bytes_before - self.bytes_after
```

**Performance Monitoring**
```python
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def monitor_operation(operation_type, metrics):
    start_time = time.time()
    try:
        yield
    except Exception as e:
        metrics.errors += 1
        logger.error(f"Compression {operation_type} error: {e}")
        raise
    finally:
        duration = time.time() - start_time
        if operation_type == 'compression':
            metrics.compression_time += duration
        else:
            metrics.decompression_time += duration
```

### Alerting Thresholds

**Recommended Alert Conditions**
```yaml
# Prometheus alerting rules example
groups:
  - name: compression_alerts
    rules:
      - alert: CompressionRatioLow
        expr: compression_ratio > 0.9  # Less than 10% compression
        for: 15m
        annotations:
          summary: "Low compression effectiveness"
          description: "Compression ratio {{ $value }} indicates poor compression"
      
      - alert: CompressionLatencyHigh
        expr: compression_latency_p95 > 10  # 10ms P95
        for: 5m
        annotations:
          summary: "High compression latency"
      
      - alert: CompressionErrorRateHigh
        expr: compression_error_rate > 0.01  # 1% error rate
        for: 5m
        annotations:
          summary: "High compression error rate"
```

## Data Type Specific Recommendations

### JSON Data

**Optimize JSON Structure for Compression**
```python
# ❌ Poor compression - varied structure
inconsistent_json = [
    {"id": 1, "name": "Alice", "extra_field": "value"},
    {"id": 2, "full_name": "Bob", "metadata": {...}},
    {"identifier": 3, "title": "Charlie"}
]

# ✅ Good compression - consistent structure
consistent_json = [
    {"id": 1, "name": "Alice", "metadata": {"extra": "value"}},
    {"id": 2, "name": "Bob", "metadata": {"full_name": "Bob Smith"}},
    {"id": 3, "name": "Charlie", "metadata": {"title": "Manager"}}
]
```

**JSON Compression Settings**
```python
json_optimized_config = CompressionConfiguration(
    enabled=True,
    compression_level=4,  # JSON compresses well, can use higher level
    min_compression_size=128,  # JSON objects are typically larger
    max_compression_size=5*1024*1024  # 5MB limit for large JSON
)
```

### Binary Data

**Handle Binary Data Appropriately**
```python
def should_compress_binary(data, sample_size=1024):
    """Determine if binary data is worth compressing."""
    if len(data) < sample_size:
        sample = data
    else:
        sample = data[:sample_size]
    
    # Simple entropy check
    unique_bytes = len(set(sample))
    entropy_ratio = unique_bytes / len(sample)
    
    # High entropy (> 0.8) suggests already compressed/encrypted data
    return entropy_ratio < 0.8

# Use with conditional compression
if should_compress_binary(binary_data):
    config = CompressionConfiguration(enabled=True)
else:
    config = CompressionConfiguration(enabled=False)
```

### Time Series Data

**Time Series Optimization**
```python
# Structure time series for better compression
time_series_data = {
    "metric": "cpu_usage",
    "timestamps": [1640995200, 1640995260, 1640995320, ...],  # Regular intervals
    "values": [45.2, 46.1, 44.8, ...],  # Similar value ranges
    "metadata": {"host": "server1", "region": "us-east"}  # Repeated metadata
}

time_series_config = CompressionConfiguration(
    enabled=True,
    compression_level=5,  # Time series data compresses very well
    min_compression_size=256,  # Time series are typically larger
    max_compression_size=20*1024*1024  # 20MB for large time series
)
```

## Testing and Validation

### Compression Testing Strategy

**Unit Tests for Compression**
```python
import pytest

class TestCompression:
    @pytest.mark.asyncio
    async def test_compression_roundtrip(self):
        """Test data integrity with compression."""
        config = CompressionConfiguration(enabled=True)
        client = await create_client_with_compression(config)
        
        test_data = "test data" * 100
        await client.set("test_key", test_data)
        retrieved = await client.get("test_key")
        
        assert retrieved == test_data
    
    @pytest.mark.asyncio
    async def test_mixed_client_compatibility(self):
        """Test compatibility between compressed and uncompressed clients."""
        compressed_client = await create_client_with_compression(
            CompressionConfiguration(enabled=True)
        )
        uncompressed_client = await create_client_with_compression(
            CompressionConfiguration(enabled=False)
        )
        
        # Test both directions
        test_data = "compatibility test" * 50
        
        # Compressed client writes, uncompressed client reads
        await compressed_client.set("test1", test_data)
        raw_data = await uncompressed_client.get("test1")
        assert raw_data != test_data  # Should be compressed
        
        # Uncompressed client writes, compressed client reads
        await uncompressed_client.set("test2", test_data)
        decompressed_data = await compressed_client.get("test2")
        assert decompressed_data == test_data  # Should be unchanged
```

**Performance Benchmarking**
```python
import asyncio
import time
from statistics import mean, stdev

async def benchmark_compression(client, data_sizes, iterations=100):
    """Benchmark compression performance across different data sizes."""
    results = {}
    
    for size in data_sizes:
        test_data = "x" * size
        set_times = []
        get_times = []
        
        for i in range(iterations):
            # Benchmark SET
            start = time.time()
            await client.set(f"bench_{size}_{i}", test_data)
            set_times.append(time.time() - start)
            
            # Benchmark GET
            start = time.time()
            await client.get(f"bench_{size}_{i}")
            get_times.append(time.time() - start)
        
        results[size] = {
            'set_mean': mean(set_times) * 1000,  # Convert to ms
            'set_stdev': stdev(set_times) * 1000,
            'get_mean': mean(get_times) * 1000,
            'get_stdev': stdev(get_times) * 1000
        }
    
    return results
```

### Load Testing

**Compression Under Load**
```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def load_test_compression(client, concurrent_operations=100, duration_seconds=60):
    """Load test compression performance."""
    start_time = time.time()
    operations_completed = 0
    errors = 0
    
    async def worker():
        nonlocal operations_completed, errors
        while time.time() - start_time < duration_seconds:
            try:
                test_data = f"load_test_data_{time.time()}" * 100
                await client.set(f"load_test_{operations_completed}", test_data)
                await client.get(f"load_test_{operations_completed}")
                operations_completed += 1
            except Exception as e:
                errors += 1
                logger.error(f"Load test error: {e}")
    
    # Run concurrent workers
    tasks = [worker() for _ in range(concurrent_operations)]
    await asyncio.gather(*tasks)
    
    return {
        'operations_per_second': operations_completed / duration_seconds,
        'error_rate': errors / (operations_completed + errors) if operations_completed + errors > 0 else 0,
        'total_operations': operations_completed,
        'total_errors': errors
    }
```

## Troubleshooting Common Issues

### Performance Degradation

**Symptoms and Solutions**

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| High CPU usage | Compression level too high | Reduce compression_level to 1-3 |
| Increased latency | Compressing small values | Increase min_compression_size |
| Memory growth | Large values being compressed | Set max_compression_size limit |
| Poor compression ratio | Incompressible data | Analyze data types, adjust thresholds |

**Diagnostic Code**
```python
async def diagnose_compression_performance(client, sample_keys):
    """Diagnose compression performance issues."""
    diagnostics = {
        'small_values_compressed': 0,
        'large_values_compressed': 0,
        'incompressible_data': 0,
        'total_operations': 0
    }
    
    for key in sample_keys:
        value = await client.get(key)
        if value:
            size = len(value.encode() if isinstance(value, str) else value)
            diagnostics['total_operations'] += 1
            
            if size < 64:
                diagnostics['small_values_compressed'] += 1
            elif size > 10*1024*1024:  # 10MB
                diagnostics['large_values_compressed'] += 1
            
            # Check if data looks incompressible (high entropy)
            if isinstance(value, (bytes, str)):
                sample = value[:1024] if len(value) > 1024 else value
                unique_chars = len(set(sample))
                if unique_chars / len(sample) > 0.8:
                    diagnostics['incompressible_data'] += 1
    
    return diagnostics
```

### Configuration Issues

**Common Misconfigurations**
```python
# ❌ Common mistakes
bad_configs = [
    # Compression level too high for high-throughput
    CompressionConfiguration(enabled=True, compression_level=22),
    
    # Threshold too low, compressing tiny values
    CompressionConfiguration(enabled=True, min_compression_size=1),
    
    # No size limit, risking memory issues
    CompressionConfiguration(enabled=True, max_compression_size=None),
    
    # Inconsistent settings across services
    # Service A: compression_level=1
    # Service B: compression_level=9
]

# ✅ Better configurations
good_configs = [
    # High-throughput service
    CompressionConfiguration(
        enabled=True,
        compression_level=2,
        min_compression_size=128,
        max_compression_size=5*1024*1024
    ),
    
    # Storage-optimized service
    CompressionConfiguration(
        enabled=True,
        compression_level=4,
        min_compression_size=64,
        max_compression_size=50*1024*1024
    )
]
```

## Security Considerations

### Data Sensitivity

**Compression and Encryption**
```python
# When using compression with encrypted data
def compress_then_encrypt(data, compression_config, encryption_key):
    """Compress first, then encrypt for better security."""
    # 1. Compress the plaintext data
    compressed_data = compress_with_config(data, compression_config)
    
    # 2. Encrypt the compressed data
    encrypted_data = encrypt(compressed_data, encryption_key)
    
    return encrypted_data

# ❌ Don't encrypt then compress - poor compression ratio
# ✅ Compress then encrypt - good compression + security
```

**Sensitive Data Handling**
```python
class SecureCompressionConfig:
    @staticmethod
    def get_config_for_data_type(data_type):
        """Get compression config based on data sensitivity."""
        if data_type in ['pii', 'financial', 'medical']:
            # More conservative settings for sensitive data
            return CompressionConfiguration(
                enabled=True,
                compression_level=1,  # Faster processing
                min_compression_size=256,  # Higher threshold
                max_compression_size=1024*1024  # 1MB limit
            )
        else:
            # Standard settings for non-sensitive data
            return CompressionConfiguration(
                enabled=True,
                compression_level=3,
                min_compression_size=64,
                max_compression_size=10*1024*1024
            )
```

## Summary

### Quick Reference

**Configuration Quick Start**
```python
# Development
dev_config = CompressionConfiguration(enabled=True, compression_level=1)

# Production (balanced)
prod_config = CompressionConfiguration(
    enabled=True,
    compression_level=3,
    min_compression_size=64,
    max_compression_size=10*1024*1024
)

# High-performance
perf_config = CompressionConfiguration(
    enabled=True,
    compression_level=1,
    min_compression_size=128
)

# Storage-optimized
storage_config = CompressionConfiguration(
    enabled=True,
    compression_level=6,
    min_compression_size=32
)
```

**Key Takeaways**

1. **Start Conservative**: Begin with low compression levels and higher size thresholds
2. **Monitor Performance**: Track compression ratio, latency, and error rates
3. **Test Thoroughly**: Validate data integrity and performance under load
4. **Optimize Gradually**: Adjust settings based on production metrics
5. **Plan for Rollback**: Always have a plan to disable compression if needed

By following these best practices, you can effectively leverage automatic compression to reduce bandwidth usage and storage requirements while maintaining optimal application performance and reliability.
