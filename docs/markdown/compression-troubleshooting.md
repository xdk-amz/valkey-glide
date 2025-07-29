# Compression Troubleshooting Guide

This guide helps you diagnose and resolve issues with the automatic compression feature in Valkey GLIDE.

## Quick Diagnostics

### Is Compression Working?

To verify compression is working, check if large values are being compressed:

=== "Python"

    ```python
    import asyncio
    from glide import GlideClient, GlideClientConfiguration, CompressionConfiguration, CompressionBackend

    async def test_compression():
        # Create client with compression
        config = GlideClientConfiguration(
            addresses=[{"host": "localhost", "port": 6379}],
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                min_compression_size=10  # Low threshold for testing
            )
        )
        client = await GlideClient.create(config)
        
        # Test with compressible data
        test_data = "A" * 1000  # 1000 bytes of repeated character
        await client.set("test_key", test_data)
        
        # Get raw value to check if compressed
        raw_value = await client.get("test_key")
        print(f"Original size: {len(test_data)}")
        print(f"Retrieved size: {len(raw_value)}")
        print(f"Values match: {raw_value == test_data}")
        
        # Check if raw storage is compressed (using different client)
        no_compression_config = GlideClientConfiguration(
            addresses=[{"host": "localhost", "port": 6379}],
            compression=CompressionConfiguration(enabled=False)
        )
        raw_client = await GlideClient.create(no_compression_config)
        raw_stored = await raw_client.get("test_key")
        
        print(f"Raw stored size: {len(raw_stored) if raw_stored else 0}")
        print(f"Is compressed: {len(raw_stored) < len(test_data) if raw_stored else False}")
        
        await client.close()
        await raw_client.close()

    asyncio.run(test_compression())
    ```

=== "TypeScript"

    ```typescript
    import { GlideClient, CompressionConfiguration, CompressionBackend } from "@valkey/valkey-glide";

    async function testCompression() {
        // Create client with compression
        const client = await GlideClient.createClient({
            addresses: [{ host: "localhost", port: 6379 }],
            compression: {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 10  // Low threshold for testing
            }
        });
        
        // Test with compressible data
        const testData = "A".repeat(1000);  // 1000 bytes of repeated character
        await client.set("test_key", testData);
        
        // Get value to verify decompression
        const retrievedValue = await client.get("test_key");
        console.log(`Original size: ${testData.length}`);
        console.log(`Retrieved size: ${retrievedValue?.length || 0}`);
        console.log(`Values match: ${retrievedValue === testData}`);
        
        // Check raw storage with non-compression client
        const rawClient = await GlideClient.createClient({
            addresses: [{ host: "localhost", port: 6379 }],
            compression: { enabled: false }
        });
        
        const rawStored = await rawClient.get("test_key");
        console.log(`Raw stored size: ${rawStored?.length || 0}`);
        console.log(`Is compressed: ${(rawStored?.length || 0) < testData.length}`);
        
        client.close();
        rawClient.close();
    }

    testCompression();
    ```

## Common Issues and Solutions

### 1. Values Not Being Compressed

**Symptoms:**
- Large values show no size reduction
- Network traffic unchanged
- Storage usage unchanged

**Possible Causes & Solutions:**

#### Compression Not Enabled
```python
# ❌ Wrong - compression disabled by default
config = GlideClientConfiguration(addresses=[...])

# ✅ Correct - explicitly enable compression
config = GlideClientConfiguration(
    addresses=[...],
    compression=CompressionConfiguration(enabled=True)
)
```

#### Value Size Below Threshold
```python
# ❌ Wrong - value too small (default threshold is 64 bytes)
await client.set("key", "small")  # Only 5 bytes

# ✅ Correct - adjust threshold or use larger values
config = CompressionConfiguration(
    enabled=True,
    min_compression_size=4  # Lower threshold
)
# OR use larger values that exceed default threshold
await client.set("key", "large_value_" * 100)
```

#### Wrong Command Type
```python
# ❌ These commands don't compress values
await client.delete("key")
await client.exists("key")
await client.expire("key", 60)

# ✅ These commands compress values
await client.set("key", value)
await client.mset({"key1": value1, "key2": value2})
await client.hset("hash", "field", value)
```

#### Data Already Compressed
```python
# ❌ Already compressed data won't compress further
import gzip
compressed_data = gzip.compress(b"original data")
await client.set("key", compressed_data)  # Little to no compression benefit

# ✅ Use uncompressed data
await client.set("key", "original data")  # Will be compressed automatically
```

### 2. Decompression Errors

**Symptoms:**
- `DecompressionError` exceptions
- Corrupted data returned
- Unexpected binary data

**Possible Causes & Solutions:**

#### Data Corruption
```python
# Check data integrity
try:
    value = await client.get("key")
except DecompressionError as e:
    print(f"Decompression failed: {e}")
    # Get raw data to inspect
    raw_client = await GlideClient.create(GlideClientConfiguration(
        addresses=[...],
        compression=CompressionConfiguration(enabled=False)
    ))
    raw_data = await raw_client.get("key")
    print(f"Raw data: {raw_data[:20]}...")  # First 20 bytes
```

#### Backend Mismatch
```python
# ❌ Wrong - trying to decompress with different backend
# Data compressed with ZSTD, client configured for different backend
config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.LZ4  # Wrong backend
)

# ✅ Correct - use same backend as used for compression
config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD  # Correct backend
)
```

#### Mixed Client Scenarios
```python
# When compression-disabled client reads compressed data
no_compression_client = await GlideClient.create(GlideClientConfiguration(
    addresses=[...],
    compression=CompressionConfiguration(enabled=False)
))

# This returns raw compressed bytes, not decompressed data
raw_compressed = await no_compression_client.get("compressed_key")
print(f"Raw compressed data: {raw_compressed}")
```

### 3. Performance Issues

**Symptoms:**
- Increased latency
- High CPU usage
- Reduced throughput

**Possible Causes & Solutions:**

#### Compression Level Too High
```python
# ❌ Wrong - high compression level for latency-sensitive app
config = CompressionConfiguration(
    enabled=True,
    compression_level=22  # Maximum compression, very slow
)

# ✅ Correct - use lower compression level for better performance
config = CompressionConfiguration(
    enabled=True,
    compression_level=1  # Fast compression
)
```

#### Compressing Small Values
```python
# ❌ Wrong - compressing small values adds overhead
config = CompressionConfiguration(
    enabled=True,
    min_compression_size=1  # Too low
)

# ✅ Correct - set appropriate threshold
config = CompressionConfiguration(
    enabled=True,
    min_compression_size=128  # Skip small values
)
```

#### Compressing Incompressible Data
```python
# ❌ Wrong - trying to compress random/binary data
import os
random_data = os.urandom(1000)  # Random bytes don't compress well
await client.set("key", random_data)

# ✅ Better - set max size limit or detect data type
config = CompressionConfiguration(
    enabled=True,
    max_compression_size=10000,  # Limit max size
    min_compression_size=100     # Skip small values
)
```

### 4. Configuration Errors

**Symptoms:**
- Client creation fails
- `ConfigurationError` exceptions
- Invalid parameter errors

**Common Configuration Fixes:**

```python
# ❌ Wrong configurations
config = CompressionConfiguration(
    enabled=True,
    compression_level=-1,  # Invalid level
    min_compression_size=-10,  # Negative size
    max_compression_size=10,   # Max < min
    backend="invalid_backend"  # Invalid backend
)

# ✅ Correct configurations
config = CompressionConfiguration(
    enabled=True,
    compression_level=3,        # Valid level (1-22 for ZSTD)
    min_compression_size=64,    # Positive size
    max_compression_size=1024*1024,  # Max > min
    backend=CompressionBackend.ZSTD  # Valid backend
)
```

## Debugging Tools

### Enable Debug Logging

=== "Python"

    ```python
    import logging
    
    # Enable debug logging for compression
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('glide.compression')
    logger.setLevel(logging.DEBUG)
    
    # Now compression operations will log debug information
    client = await GlideClient.create(config)
    await client.set("key", "value")  # Will log compression details
    ```

=== "TypeScript"

    ```typescript
    import { Logger } from "@valkey/valkey-glide";
    
    // Enable debug logging
    Logger.setLoggerConfig({ 
        level: "debug",
        destination: "console"
    });
    
    // Now compression operations will log debug information
    const client = await GlideClient.createClient(config);
    await client.set("key", "value");  // Will log compression details
    ```

### Compression Statistics

Monitor compression effectiveness:

```python
async def monitor_compression(client):
    # Test different data types
    test_cases = [
        ("json", '{"name": "test", "data": "' + "x" * 1000 + '"}'),
        ("text", "The quick brown fox " * 100),
        ("binary", bytes(range(256)) * 10),
        ("random", os.urandom(1000))
    ]
    
    for name, data in test_cases:
        # Measure with compression
        start_time = time.time()
        await client.set(f"test_{name}", data)
        compress_time = time.time() - start_time
        
        start_time = time.time()
        result = await client.get(f"test_{name}")
        decompress_time = time.time() - start_time
        
        # Measure raw size
        raw_client = await GlideClient.create(no_compression_config)
        raw_data = await raw_client.get(f"test_{name}")
        
        print(f"{name}:")
        print(f"  Original size: {len(data)}")
        print(f"  Compressed size: {len(raw_data) if raw_data else 0}")
        print(f"  Compression ratio: {len(raw_data)/len(data)*100:.1f}%")
        print(f"  Compress time: {compress_time*1000:.2f}ms")
        print(f"  Decompress time: {decompress_time*1000:.2f}ms")
        print(f"  Data integrity: {result == data}")
        print()
```

### Network Traffic Analysis

Monitor network usage to verify compression benefits:

```bash
# Monitor network traffic to Redis server
sudo tcpdump -i any -s 0 -w redis_traffic.pcap host localhost and port 6379

# Analyze captured traffic
wireshark redis_traffic.pcap
```

## Error Reference

### CompressionError Types

| Error | Description | Common Causes | Solutions |
|-------|-------------|---------------|-----------|
| `CompressionFailed` | Compression operation failed | Invalid data, memory issues | Check data format, increase memory |
| `DecompressionFailed` | Decompression operation failed | Corrupted data, wrong backend | Verify data integrity, check backend |
| `UnsupportedBackend` | Compression backend not available | Invalid backend name | Use supported backend (ZSTD) |
| `InvalidConfiguration` | Configuration parameters invalid | Wrong parameter values | Validate configuration parameters |
| `BackendInitializationFailed` | Backend failed to initialize | Missing dependencies, system issues | Check system requirements |

### Configuration Validation

Validate your compression configuration:

```python
def validate_compression_config(config: CompressionConfiguration):
    """Validate compression configuration parameters."""
    errors = []
    
    if config.compression_level is not None:
        if config.backend == CompressionBackend.ZSTD:
            if not (1 <= config.compression_level <= 22):
                errors.append("ZSTD compression level must be 1-22")
    
    if config.min_compression_size < 0:
        errors.append("min_compression_size must be non-negative")
    
    if config.max_compression_size is not None:
        if config.max_compression_size < config.min_compression_size:
            errors.append("max_compression_size must be >= min_compression_size")
    
    if errors:
        raise ValueError("Configuration errors: " + "; ".join(errors))
    
    return True

# Usage
try:
    validate_compression_config(your_config)
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Performance Tuning

### Optimal Settings by Use Case

**High-throughput, low-latency:**
```python
CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=1,      # Fastest
    min_compression_size=256, # Skip small values
    max_compression_size=64*1024  # Limit large values
)
```

**Storage optimization:**
```python
CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=6,      # Better compression
    min_compression_size=32,  # Compress more values
    max_compression_size=None # No size limit
)
```

**Balanced (recommended):**
```python
CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=3,      # Good balance
    min_compression_size=64,  # Standard threshold
    max_compression_size=1024*1024  # 1MB limit
)
```

## Getting Help

If you continue to experience issues:

1. **Check logs** for detailed error messages
2. **Test with minimal configuration** to isolate the problem
3. **Verify server compatibility** (any Redis/Valkey version works)
4. **Check network connectivity** and data integrity
5. **Review configuration** against this troubleshooting guide

For additional support:
- [GitHub Issues](https://github.com/valkey-io/valkey-glide/issues)
- [Documentation](https://valkey.io/valkey-glide)
- [Community Forums](https://github.com/valkey-io/valkey-glide/discussions)
