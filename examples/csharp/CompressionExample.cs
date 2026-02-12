// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

/// <summary>
/// Compression Example
///
/// This example demonstrates how to create GLIDE clients with compression
/// configurations for both standalone and cluster modes.
///
/// Compression is transparent — values that meet the minimum size threshold
/// are automatically compressed before being sent to the server and
/// decompressed when retrieved. Compressed and uncompressed clients can
/// interoperate seamlessly.
/// </summary>

using Glide;

// ============================================================
// Example 1: Standalone client with ZSTD compression (default)
// ============================================================

var zstdCompression = new CompressionConfiguration(
    enabled: true,
    backend: CompressionBackend.Zstd,
    compressionLevel: 3,       // ZSTD default level
    minCompressionSize: 64     // Only compress values >= 64 bytes
);

var standaloneConfig = new GlideClientConfiguration(
    addresses: new[] { new NodeAddress("localhost", 6379) },
    compression: zstdCompression
);

Console.WriteLine("Standalone client configuration with ZSTD compression:");
Console.WriteLine($"  Enabled: {standaloneConfig.Compression!.Enabled}");
Console.WriteLine($"  Backend: {standaloneConfig.Compression.Backend}");
Console.WriteLine($"  Level: {standaloneConfig.Compression.CompressionLevel}");
Console.WriteLine($"  Min Size: {standaloneConfig.Compression.MinCompressionSize} bytes");
Console.WriteLine();

// ============================================================
// Example 2: Cluster client with LZ4 compression
// ============================================================

var lz4Compression = new CompressionConfiguration(
    enabled: true,
    backend: CompressionBackend.Lz4,
    compressionLevel: 0,       // LZ4 default level
    minCompressionSize: 128    // Only compress values >= 128 bytes
);

var clusterConfig = new GlideClusterClientConfiguration(
    addresses: new[]
    {
        new NodeAddress("node1.example.com", 6379),
        new NodeAddress("node2.example.com", 6379),
        new NodeAddress("node3.example.com", 6379),
    },
    compression: lz4Compression
);

Console.WriteLine("Cluster client configuration with LZ4 compression:");
Console.WriteLine($"  Enabled: {clusterConfig.Compression!.Enabled}");
Console.WriteLine($"  Backend: {clusterConfig.Compression.Backend}");
Console.WriteLine($"  Level: {clusterConfig.Compression.CompressionLevel}");
Console.WriteLine($"  Min Size: {clusterConfig.Compression.MinCompressionSize} bytes");
Console.WriteLine();

// ============================================================
// Example 3: Compression with backend default level
// ============================================================

var defaultLevelCompression = new CompressionConfiguration(
    enabled: true,
    backend: CompressionBackend.Zstd
    // compressionLevel omitted — uses backend default (3 for ZSTD)
    // minCompressionSize omitted — uses default (64 bytes)
);

Console.WriteLine("Compression with backend default level:");
Console.WriteLine($"  Level: {(defaultLevelCompression.CompressionLevel?.ToString() ?? "backend default")}");
Console.WriteLine($"  Min Size: {defaultLevelCompression.MinCompressionSize} bytes");
Console.WriteLine();

// ============================================================
// Example 4: Client without compression (default behavior)
// ============================================================

var noCompressionConfig = new GlideClientConfiguration(
    addresses: new[] { new NodeAddress("localhost", 6379) }
);

Console.WriteLine($"Client without compression: Compression is {(noCompressionConfig.Compression == null ? "not configured" : "configured")}");
Console.WriteLine();

// ============================================================
// Example 5: Setting compression after client config creation
// ============================================================

var config = new GlideClientConfiguration(
    addresses: new[] { new NodeAddress("localhost", 6379) }
);

// Compression can be set after initial configuration
config.Compression = new CompressionConfiguration(
    enabled: true,
    backend: CompressionBackend.Zstd,
    compressionLevel: 5,
    minCompressionSize: 256
);

Console.WriteLine("Compression set after config creation:");
Console.WriteLine($"  Enabled: {config.Compression.Enabled}");
Console.WriteLine($"  Level: {config.Compression.CompressionLevel}");
Console.WriteLine($"  Min Size: {config.Compression.MinCompressionSize} bytes");
Console.WriteLine();

// ============================================================
// Example 6: Protobuf serialization for FFI
// ============================================================

var bytes = ConnectionRequestSerializer.Serialize(standaloneConfig, clusterMode: false);
Console.WriteLine($"Serialized ConnectionRequest: {bytes.Length} bytes");
Console.WriteLine();

// ============================================================
// Example 7: Statistics usage
// ============================================================

// In a real application, statistics would be retrieved from the FFI layer.
// This demonstrates the Statistics class structure.
var stats = new Statistics
{
    TotalConnections = 3,
    TotalClients = 1,
    TotalValuesCompressed = 150,
    TotalValuesDecompressed = 120,
    TotalOriginalBytes = 500000,
    TotalBytesCompressed = 125000,
    TotalBytesDecompressed = 500000,
    CompressionSkippedCount = 30,
};

Console.WriteLine("Compression Statistics:");
Console.WriteLine($"  Values compressed: {stats.TotalValuesCompressed}");
Console.WriteLine($"  Values decompressed: {stats.TotalValuesDecompressed}");
Console.WriteLine($"  Original bytes: {stats.TotalOriginalBytes}");
Console.WriteLine($"  Compressed bytes: {stats.TotalBytesCompressed}");
Console.WriteLine($"  Compression ratio: {(double)stats.TotalOriginalBytes / stats.TotalBytesCompressed:F2}x");
Console.WriteLine($"  Skipped: {stats.CompressionSkippedCount}");
Console.WriteLine();

var dict = stats.ToDictionary();
Console.WriteLine($"Statistics as dictionary ({dict.Count} entries):");
foreach (var (key, value) in dict)
{
    Console.WriteLine($"  {key}: {value}");
}

Console.WriteLine();
Console.WriteLine("Compression example completed successfully.");
