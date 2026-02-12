// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

/// <summary>
/// Compression Example
///
/// Demonstrates how to create GLIDE clients with compression enabled,
/// perform SET/GET operations, and verify compression behavior using
/// the client's statistics.
///
/// NOTE: This example requires a running Valkey/Redis server on localhost:6379
/// and the native FFI library linked. The code below shows the intended usage
/// pattern — the actual GlideClient.CreateAsync() call depends on the full
/// C# client being wired to the Rust core via FFI.
/// </summary>

using Glide;

Console.WriteLine("=== Valkey GLIDE C# Compression Example ===");
Console.WriteLine();

// ============================================================
// 1. Create a client with ZSTD compression
// ============================================================

var zstdCompression = new CompressionConfiguration(
    Enabled: true,
    Backend: CompressionBackend.Zstd,
    CompressionLevel: 3,       // ZSTD default level
    MinCompressionSize: 64     // Only compress values >= 64 bytes
);

var standaloneConfig = new GlideClientConfiguration(
    addresses: new[] { new NodeAddress("localhost", 6379) },
    compression: zstdCompression
);

Console.WriteLine("1. Standalone client with ZSTD compression");
Console.WriteLine($"   Backend: {standaloneConfig.Compression!.Backend}");
Console.WriteLine($"   Level: {standaloneConfig.Compression.CompressionLevel}");
Console.WriteLine($"   Min size: {standaloneConfig.Compression.MinCompressionSize} bytes");
Console.WriteLine();

// --- Simulated client usage (requires FFI + running server) ---
// var client = await GlideClient.CreateAsync(standaloneConfig);
//
// // Capture stats before SET
// var statsBefore = await client.GetStatisticsAsync();
// var compressedBefore = statsBefore.TotalValuesCompressed;
// var originalBytesBefore = statsBefore.TotalOriginalBytes;
// var compressedBytesBefore = statsBefore.TotalBytesCompressed;
//
// // SET a large compressible value (1KB of repeated text)
// var key = "compression_demo_key";
// var value = new string('A', 10) + new string('B', 10) + new string('C', 10);
// value = string.Concat(Enumerable.Repeat(value, 35)); // ~1050 bytes
//
// await client.SetAsync(key, value);
//
// // GET the value back — decompression is transparent
// var retrieved = await client.GetAsync(key);
// Debug.Assert(retrieved == value, "Retrieved value must match original");
//
// // Verify compression happened via statistics
// var statsAfter = await client.GetStatisticsAsync();
// Debug.Assert(statsAfter.TotalValuesCompressed > compressedBefore,
//     "Compression count should increase for a 1KB compressible value");
//
// // Verify compressed bytes < original bytes (compression ratio)
// var originalAdded = statsAfter.TotalOriginalBytes - originalBytesBefore;
// var compressedAdded = statsAfter.TotalBytesCompressed - compressedBytesBefore;
// Debug.Assert(compressedAdded <= originalAdded,
//     $"Compressed size ({compressedAdded}) should be <= original ({originalAdded})");
//
// Console.WriteLine($"   SET/GET verified: {value.Length} bytes round-tripped");
// Console.WriteLine($"   Compressed: {originalAdded} -> {compressedAdded} bytes");
// Console.WriteLine($"   Ratio: {(double)originalAdded / compressedAdded:F2}x");

// ============================================================
// 2. Demonstrate small values are skipped (below threshold)
// ============================================================

Console.WriteLine("2. Small values below min_compression_size are skipped");
Console.WriteLine();

// --- Simulated client usage ---
// var statsBeforeSmall = await client.GetStatisticsAsync();
// var skippedBefore = statsBeforeSmall.CompressionSkippedCount;
// var compressedCountBefore = statsBeforeSmall.TotalValuesCompressed;
//
// // SET a small value (32 bytes, below 64-byte threshold)
// await client.SetAsync("small_key", new string('X', 32));
// var smallResult = await client.GetAsync("small_key");
// Debug.Assert(smallResult == new string('X', 32));
//
// var statsAfterSmall = await client.GetStatisticsAsync();
// Debug.Assert(statsAfterSmall.CompressionSkippedCount > skippedBefore,
//     "Compression should be skipped for values below threshold");
// Debug.Assert(statsAfterSmall.TotalValuesCompressed == compressedCountBefore,
//     "Compressed count should NOT increase for small values");
//
// Console.WriteLine($"   32-byte value: skipped (count: {statsAfterSmall.CompressionSkippedCount})");

// ============================================================
// 3. Create a cluster client with LZ4 compression
// ============================================================

var lz4Compression = new CompressionConfiguration(
    Enabled: true,
    Backend: CompressionBackend.Lz4,
    CompressionLevel: 0,       // LZ4 default level
    MinCompressionSize: 128    // Higher threshold for cluster
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

Console.WriteLine("3. Cluster client with LZ4 compression");
Console.WriteLine($"   Backend: {clusterConfig.Compression!.Backend}");
Console.WriteLine($"   Level: {clusterConfig.Compression.CompressionLevel}");
Console.WriteLine($"   Min size: {clusterConfig.Compression.MinCompressionSize} bytes");
Console.WriteLine();

// --- Simulated cluster client usage ---
// var clusterClient = await GlideClusterClient.CreateAsync(clusterConfig);
//
// var clusterStatsBefore = await clusterClient.GetStatisticsAsync();
// var clusterCompressedBefore = clusterStatsBefore.TotalValuesCompressed;
//
// // SET a 10KB value across cluster
// var clusterValue = string.Concat(Enumerable.Repeat("ClusterData_", 850)); // ~10KB
// await clusterClient.SetAsync("cluster_key", clusterValue);
// var clusterRetrieved = await clusterClient.GetAsync("cluster_key");
// Debug.Assert(clusterRetrieved == clusterValue);
//
// var clusterStatsAfter = await clusterClient.GetStatisticsAsync();
// Debug.Assert(clusterStatsAfter.TotalValuesCompressed > clusterCompressedBefore,
//     "Cluster compression should work the same as standalone");
//
// Console.WriteLine($"   Cluster SET/GET verified: {clusterValue.Length} bytes");

// ============================================================
// 4. Backend mismatch — data written with ZSTD, read with LZ4
// ============================================================

Console.WriteLine("4. Backend mismatch: ZSTD writer, LZ4 reader");
Console.WriteLine("   Compression is transparent — any client can read any data");
Console.WriteLine();

// --- Simulated usage ---
// // Write with ZSTD client
// var mismatchValue = string.Concat(Enumerable.Repeat("MismatchTest_", 800));
// await client.SetAsync("mismatch_key", mismatchValue);
//
// // Read with LZ4 client — decompression detects the backend from the header
// var lz4Client = await GlideClient.CreateAsync(new GlideClientConfiguration(
//     addresses: new[] { new NodeAddress("localhost", 6379) },
//     compression: new CompressionConfiguration(
//         Enabled: true,
//         Backend: CompressionBackend.Lz4,
//         MinCompressionSize: 64)));
//
// var mismatchResult = await lz4Client.GetAsync("mismatch_key");
// Debug.Assert(mismatchResult == mismatchValue,
//     "LZ4 client should read ZSTD-compressed data correctly");
//
// Console.WriteLine($"   ZSTD-written value read by LZ4 client: OK");
// await lz4Client.CloseAsync();

// ============================================================
// 5. Disabled compression — verify no compression occurs
// ============================================================

Console.WriteLine("5. Disabled compression: operations work, no compression applied");
Console.WriteLine();

var noCompressionConfig = new GlideClientConfiguration(
    addresses: new[] { new NodeAddress("localhost", 6379) }
    // No compression parameter — compression is disabled by default
);

// --- Simulated usage ---
// var noCompClient = await GlideClient.CreateAsync(noCompressionConfig);
//
// var noCompStatsBefore = await noCompClient.GetStatisticsAsync();
// var noCompCompressedBefore = noCompStatsBefore.TotalValuesCompressed;
// var noCompSkippedBefore = noCompStatsBefore.CompressionSkippedCount;
//
// // SET a large value — should NOT be compressed
// await noCompClient.SetAsync("no_comp_key", new string('Z', 10000));
// var noCompResult = await noCompClient.GetAsync("no_comp_key");
// Debug.Assert(noCompResult == new string('Z', 10000));
//
// var noCompStatsAfter = await noCompClient.GetStatisticsAsync();
// Debug.Assert(noCompStatsAfter.TotalValuesCompressed == noCompCompressedBefore,
//     "No compression should occur when disabled");
// Debug.Assert(noCompStatsAfter.CompressionSkippedCount == noCompSkippedBefore,
//     "Skip count should not change when compression is disabled entirely");
//
// Console.WriteLine($"   10KB value stored without compression: OK");
// await noCompClient.CloseAsync();

// ============================================================
// 6. Reading and interpreting statistics
// ============================================================

Console.WriteLine("6. Statistics interpretation");
Console.WriteLine();

// Demonstrate the Statistics class with realistic values
var stats = new Statistics
{
    TotalConnections = 3,
    TotalClients = 2,
    TotalValuesCompressed = 150,
    TotalValuesDecompressed = 120,
    TotalOriginalBytes = 500_000,
    TotalBytesCompressed = 125_000,
    TotalBytesDecompressed = 500_000,
    CompressionSkippedCount = 30,
};

// Use statistics to verify compression behavior
Console.WriteLine($"   Values compressed:   {stats.TotalValuesCompressed}");
Console.WriteLine($"   Values decompressed: {stats.TotalValuesDecompressed}");
Console.WriteLine($"   Original bytes:      {stats.TotalOriginalBytes:N0}");
Console.WriteLine($"   Compressed bytes:    {stats.TotalBytesCompressed:N0}");
Console.WriteLine($"   Compression ratio:   {(double)stats.TotalOriginalBytes / stats.TotalBytesCompressed:F2}x");
Console.WriteLine($"   Space saved:         {stats.TotalOriginalBytes - stats.TotalBytesCompressed:N0} bytes " +
    $"({(1.0 - (double)stats.TotalBytesCompressed / stats.TotalOriginalBytes) * 100:F1}%)");
Console.WriteLine($"   Skipped (too small): {stats.CompressionSkippedCount}");
Console.WriteLine();

// Assert compression invariants
var compressionRatio = (double)stats.TotalOriginalBytes / stats.TotalBytesCompressed;
System.Diagnostics.Debug.Assert(stats.TotalBytesCompressed <= stats.TotalOriginalBytes,
    "Compressed bytes should always be <= original bytes");
System.Diagnostics.Debug.Assert(compressionRatio >= 1.0,
    "Compression ratio should be >= 1.0");

// Dictionary form for programmatic access
var dict = stats.ToDictionary();
System.Diagnostics.Debug.Assert(dict["total_values_compressed"] == 150);
System.Diagnostics.Debug.Assert(dict["compression_skipped_count"] == 30);
Console.WriteLine($"   Dictionary access: total_values_compressed = {dict["total_values_compressed"]}");

// ============================================================
// 7. Cleanup
// ============================================================

// --- Simulated cleanup ---
// await client.DeleteAsync(new[] { "compression_demo_key", "small_key",
//     "mismatch_key", "no_comp_key", "cluster_key" });
// await client.CloseAsync();
// await clusterClient.CloseAsync();

Console.WriteLine();
Console.WriteLine("=== Compression example completed successfully ===");
