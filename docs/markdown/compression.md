# Automatic Compression Feature

Valkey GLIDE supports automatic compression and decompression of values to reduce bandwidth usage and storage requirements. This feature is completely transparent to your application code and maintains full backward compatibility with existing data.

## Overview

The compression feature automatically:

- **Compresses values** for set-type commands (SET, MSET, HSET, etc.) before sending to the server
- **Decompresses values** for get-type commands (GET, MGET, HGET, etc.) when receiving from the server
- **Maintains compatibility** with uncompressed data and non-compression clients
- **Works across all language bindings** with consistent behavior

## Configuration

Compression is configured at the client level and is disabled by default. You can enable it by providing compression configuration when creating your client.

=== "Python"

    ```python
    from glide import (
        GlideClientConfiguration, 
        GlideClusterClientConfiguration,
        CompressionConfiguration,
        CompressionBackend
    )

    # Configure compression
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=3,
        min_compression_size=64,  # Skip compression for values < 64 bytes
        max_compression_size=1024*1024  # Skip compression for values > 1MB
    )

    # Standalone client with compression
    config = GlideClientConfiguration(
        addresses=[NodeAddress("localhost", 6379)],
        compression=compression_config
    )
    client = await GlideClient.create(config)

    # Cluster client with compression
    cluster_config = GlideClusterClientConfiguration(
        addresses=[NodeAddress("localhost", 6379)],
        compression=compression_config
    )
    cluster_client = await GlideClusterClient.create(cluster_config)
    ```

=== "TypeScript"

    ```typescript
    import { 
        GlideClient, 
        GlideClusterClient,
        CompressionConfiguration,
        CompressionBackend 
    } from "@valkey/valkey-glide";

    // Configure compression
    const compressionConfig: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        compressionLevel: 3,
        minCompressionSize: 64,  // Skip compression for values < 64 bytes
        maxCompressionSize: 1024*1024  // Skip compression for values > 1MB
    };

    // Standalone client with compression
    const client = await GlideClient.createClient({
        addresses: [{ host: "localhost", port: 6379 }],
        compression: compressionConfig
    });

    // Cluster client with compression
    const clusterClient = await GlideClusterClient.createClient({
        addresses: [{ host: "localhost", port: 6379 }],
        compression: compressionConfig
    });
    ```

=== "Java"

    ```java
    import glide.api.GlideClient;
    import glide.api.GlideClusterClient;
    import glide.api.models.configuration.GlideClientConfiguration;
    import glide.api.models.configuration.GlideClusterClientConfiguration;
    import glide.api.models.configuration.CompressionConfiguration;
    import glide.api.models.configuration.CompressionBackend;

    // Configure compression
    CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
        .enabled(true)
        .backend(CompressionBackend.ZSTD)
        .compressionLevel(3)
        .minCompressionSize(64)  // Skip compression for values < 64 bytes
        .maxCompressionSize(1024*1024)  // Skip compression for values > 1MB
        .build();

    // Standalone client with compression
    GlideClientConfiguration config = GlideClientConfiguration.builder()
        .address(NodeAddress.builder().host("localhost").port(6379).build())
        .compression(compressionConfig)
        .build();
    GlideClient client = GlideClient.createClient(config).get();

    // Cluster client with compression
    GlideClusterClientConfiguration clusterConfig = GlideClusterClientConfiguration.builder()
        .address(NodeAddress.builder().host("localhost").port(6379).build())
        .compression(compressionConfig)
        .build();
    GlideClusterClient clusterClient = GlideClusterClient.createClient(clusterConfig).get();
    ```

=== "Go"

    ```go
    import (
        "github.com/valkey-io/valkey-glide/go"
        "github.com/valkey-io/valkey-glide/go/config"
    )

    // Configure compression
    compressionConfig := &config.CompressionConfig{
        Enabled:            true,
        Backend:            config.ZstdBackend,
        CompressionLevel:   3,
        MinCompressionSize: 64,        // Skip compression for values < 64 bytes
        MaxCompressionSize: 1024*1024, // Skip compression for values > 1MB
    }

    // Standalone client with compression
    clientConfig := &config.GlideClientConfiguration{
        Addresses: []config.NodeAddress{
            {Host: "localhost", Port: 6379},
        },
        Compression: compressionConfig,
    }
    client := glide.NewGlideClient(clientConfig)

    // Cluster client with compression
    clusterConfig := &config.GlideClusterClientConfiguration{
        Addresses: []config.NodeAddress{
            {Host: "localhost", Port: 6379},
        },
        Compression: compressionConfig,
    }
    clusterClient := glide.NewGlideClusterClient(clusterConfig)
    ```

=== "C#"

    ```csharp
    using Glide;
    using Glide.Config;

    // Configure compression
    var compressionConfig = new CompressionConfiguration
    {
        Enabled = true,
        Backend = CompressionBackend.Zstd,
        CompressionLevel = 3,
        MinCompressionSize = 64,        // Skip compression for values < 64 bytes
        MaxCompressionSize = 1024*1024  // Skip compression for values > 1MB
    };

    // Standalone client with compression
    var config = new GlideClientConfiguration
    {
        Addresses = new[] { new NodeAddress("localhost", 6379) },
        Compression = compressionConfig
    };
    var client = await GlideClient.CreateAsync(config);

    // Cluster client with compression
    var clusterConfig = new GlideClusterClientConfiguration
    {
        Addresses = new[] { new NodeAddress("localhost", 6379) },
        Compression = compressionConfig
    };
    var clusterClient = await GlideClusterClient.CreateAsync(clusterConfig);
    ```

## Configuration Options

### CompressionConfiguration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable/disable compression |
| `backend` | CompressionBackend | `ZSTD` | Compression algorithm to use |
| `compressionLevel` | integer | Backend default | Compression level (higher = better compression, slower) |
| `minCompressionSize` | integer | `64` | Minimum value size in bytes to compress |
| `maxCompressionSize` | integer | `null` | Maximum value size in bytes to compress (null = no limit) |

### Supported Compression Backends

| Backend | Description | Compression Level Range | Default Level |
|---------|-------------|------------------------|---------------|
| `ZSTD` | Zstandard - balanced speed and compression ratio | 1-22 | 3 |

!!! note "Future Backends"
    Additional compression backends (LZ4, etc.) may be added in future versions.

## How It Works

### Automatic Operation

When compression is enabled, the client automatically handles compression and decompression:

```python
# With compression enabled, this works exactly the same as without compression
await client.set("key", "large_value_that_will_be_compressed")
value = await client.get("key")  # Automatically decompressed
print(value)  # Original uncompressed value
```

### Command Classification

Commands are automatically classified for compression behavior:

- **Set-type commands**: Values are compressed before sending
  - `SET`, `MSET`, `HSET`, `HMSET`, `LPUSH`, `RPUSH`, etc.
- **Get-type commands**: Values are decompressed after receiving  
  - `GET`, `MGET`, `HGET`, `HMGET`, `LPOP`, `RPOP`, etc.
- **Other commands**: No compression applied
  - `DEL`, `EXISTS`, `KEYS`, etc.

### Size Thresholds

Compression is only applied when:

- Value size ≥ `minCompressionSize` (default: 64 bytes)
- Value size ≤ `maxCompressionSize` (if specified)

Small values are not compressed to avoid overhead.

### Data Format

Compressed values use a magic header format for identification:

```
[GLID][Backend ID][Compressed Data]
```

- `GLID`: 4-byte magic header (0x47, 0x4C, 0x49, 0x44)
- `Backend ID`: 1-byte backend identifier (0x01 for ZSTD)
- `Compressed Data`: The actual compressed payload

## Backward Compatibility

The compression feature is fully backward compatible:

### Mixed Client Scenarios

- **Compression-enabled client reading uncompressed data**: Works seamlessly
- **Compression-disabled client reading compressed data**: Returns raw compressed bytes
- **Different compression settings**: Each client handles data according to its configuration

### Migration Strategy

You can safely enable compression on existing applications:

1. **No server changes required**: Compression works with any Valkey/Redis server
2. **No data migration needed**: Existing uncompressed data remains accessible
3. **Gradual rollout**: Enable compression on clients incrementally
4. **Rollback friendly**: Disable compression anytime without data loss

## Performance Characteristics

### Compression Ratios

Typical compression ratios by data type:

| Data Type | Typical Ratio | Notes |
|-----------|---------------|-------|
| JSON | 60-80% | High redundancy, excellent compression |
| Plain Text | 50-70% | Good compression for repetitive text |
| Binary Data | 10-50% | Varies greatly by content |
| Already Compressed | 0-5% | Minimal benefit, may increase size |

### Performance Impact

| Operation | Typical Overhead | Notes |
|-----------|------------------|-------|
| Compression | 0.1-2ms | Depends on value size and level |
| Decompression | 0.05-1ms | Generally faster than compression |
| Network Transfer | -50% to -80% | Significant bandwidth savings |

### Tuning Guidelines

For **high throughput** scenarios:
```python
CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=1,  # Faster compression
    min_compression_size=128  # Higher threshold
)
```

For **maximum compression** scenarios:
```python
CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=6,  # Better compression
    min_compression_size=32  # Lower threshold
)
```

## Batch Operations

Compression works seamlessly with batch operations:

=== "Python"

    ```python
    # Pipeline with compression
    async with client.pipeline() as pipeline:
        pipeline.set("key1", large_value1)  # Automatically compressed
        pipeline.set("key2", large_value2)  # Automatically compressed
        pipeline.get("key1")               # Automatically decompressed
        results = await pipeline.exec()

    # Transaction with compression
    async with client.transaction() as transaction:
        transaction.mset({"key1": value1, "key2": value2})  # Values compressed
        transaction.mget(["key1", "key2"])                  # Values decompressed
        results = await transaction.exec()
    ```

=== "TypeScript"

    ```typescript
    // Pipeline with compression
    const pipeline = client.createPipeline();
    pipeline.set("key1", largeValue1);  // Automatically compressed
    pipeline.set("key2", largeValue2);  // Automatically compressed
    pipeline.get("key1");              // Automatically decompressed
    const results = await client.exec(pipeline);

    // Transaction with compression
    const transaction = client.createTransaction();
    transaction.mset({"key1": value1, "key2": value2});  // Values compressed
    transaction.mget(["key1", "key2"]);                  // Values decompressed
    const results = await client.exec(transaction);
    ```

## Error Handling

### Graceful Fallback

The compression system implements graceful fallback:

- **Compression failure**: Sends original uncompressed value + logs warning
- **Decompression failure**: Returns raw value + logs warning
- **Configuration errors**: Throws exception during client creation

### Common Error Scenarios

| Error | Cause | Resolution |
|-------|-------|------------|
| `CompressionError` | Invalid compression configuration | Check configuration parameters |
| `UnsupportedBackend` | Requested backend not available | Use supported backend (ZSTD) |
| `CompressionFailed` | Backend compression failed | Check value size and format |
| `DecompressionFailed` | Invalid compressed data | Verify data integrity |

## Troubleshooting

### Debugging Compression Issues

Enable debug logging to troubleshoot compression:

=== "Python"

    ```python
    import logging
    logging.getLogger('glide').setLevel(logging.DEBUG)
    ```

=== "TypeScript"

    ```typescript
    import { Logger } from "@valkey/valkey-glide";
    Logger.setLoggerConfig({ level: "debug" });
    ```

### Common Issues

**Issue**: Values not being compressed
- **Check**: Value size meets `minCompressionSize` threshold
- **Check**: Command type supports compression (set-type commands)
- **Check**: Compression is enabled in configuration

**Issue**: Decompression errors
- **Check**: Data was compressed with compatible backend
- **Check**: Data integrity (network/storage corruption)
- **Check**: Client compression configuration matches

**Issue**: Performance degradation
- **Check**: Compression level setting (lower = faster)
- **Check**: Size thresholds (avoid compressing small values)
- **Check**: Data compressibility (already compressed data)

### Monitoring

Monitor compression effectiveness:

```python
# Log compression statistics (implementation-specific)
client.get_compression_stats()
# Returns: {
#   "compressed_operations": 1000,
#   "decompressed_operations": 950,
#   "compression_ratio": 0.65,
#   "compression_errors": 2,
#   "decompression_errors": 1
# }
```

## Best Practices

### When to Use Compression

✅ **Good candidates for compression:**
- Large JSON payloads
- Text data with repetitive content
- Serialized objects
- High-bandwidth applications
- Storage-constrained environments

❌ **Poor candidates for compression:**
- Small values (< 64 bytes)
- Already compressed data (images, videos)
- High-frequency, low-latency operations
- Binary data with high entropy

### Configuration Recommendations

**Development/Testing:**
```python
CompressionConfiguration(
    enabled=True,
    compression_level=1,  # Fast for development
    min_compression_size=32
)
```

**Production (Balanced):**
```python
CompressionConfiguration(
    enabled=True,
    compression_level=3,  # Good balance
    min_compression_size=64,
    max_compression_size=10*1024*1024  # 10MB limit
)
```

**Production (High Compression):**
```python
CompressionConfiguration(
    enabled=True,
    compression_level=6,  # Better compression
    min_compression_size=128
)
```

### Migration Best Practices

1. **Test thoroughly** in staging environment
2. **Monitor performance** impact during rollout
3. **Enable gradually** across client instances
4. **Keep fallback plan** (disable compression if needed)
5. **Monitor error rates** for compression/decompression failures

## Limitations

- **Server-side operations**: Compression only applies to client-server communication, not server-side operations like `SORT` or Lua scripts
- **Memory usage**: Compression requires additional memory for processing
- **CPU overhead**: Compression/decompression uses CPU resources
- **Backend availability**: Only ZSTD backend currently supported

## Future Enhancements

Planned improvements include:

- Additional compression backends (LZ4, Brotli)
- Adaptive compression based on data characteristics
- Compression statistics and monitoring
- Per-command compression configuration
- Streaming compression for very large values
