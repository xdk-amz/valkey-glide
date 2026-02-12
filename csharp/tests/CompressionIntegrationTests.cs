// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using Glide;
using Xunit;

namespace Glide.Tests;

/// <summary>
/// Integration tests for compression functionality.
///
/// Tests are organized into two categories:
/// 1. Unit tests that verify configuration, serialization, and statistics plumbing
///    (these run without a server).
/// 2. Integration test stubs (marked with [Fact(Skip = ...)] ) that require a running
///    Valkey/Redis server and the native FFI library. These mirror the Python reference
///    tests in python/tests/async_tests/test_compression.py and should be enabled once
///    the C# client's FFI wiring (GlideClient.CreateAsync, SetAsync, GetAsync,
///    GetStatisticsAsync) is complete.
/// </summary>
public class CompressionIntegrationTests
{
    // ==================== Data Generation Helpers ====================

    /// <summary>Generate highly compressible text (repeated patterns).</summary>
    private static string GenerateCompressibleText(int charCount)
    {
        var pattern = new string('A', 10) + new string('B', 10) + new string('C', 10);
        var repeated = string.Concat(Enumerable.Repeat(pattern, (charCount / pattern.Length) + 1));
        return repeated[..charCount];
    }

    /// <summary>Generate JSON-like structured data.</summary>
    private static string GenerateJsonData(int charCount)
    {
        const string jsonStr = """{"id":12345,"name":"Test User","email":"test@example.com","description":"AAAAAAAAAA","metadata":{"key":"value"},"tags":["tag1","tag2","tag3"]}""";
        var repeated = string.Concat(Enumerable.Repeat(jsonStr, (charCount / jsonStr.Length) + 1));
        return repeated[..charCount];
    }

    /// <summary>Generate base64-like data (low compressibility).</summary>
    private static string GenerateBase64Data(int charCount)
    {
        var random = new Random(42); // Fixed seed for reproducibility
        var bytes = new byte[charCount / 2];
        random.NextBytes(bytes);
        var base64 = Convert.ToBase64String(bytes);
        return base64.Length >= charCount ? base64[..charCount] : base64.PadRight(charCount, '=');
    }

    /// <summary>Generate text with unicode characters.
    /// Note: charCount is the number of characters, not bytes. Unicode chars may be multi-byte.</summary>
    private static string GenerateUnicodeText(int charCount)
    {
        const string chars = "Hello世界Привет";
        var repeated = string.Concat(Enumerable.Repeat(chars, (charCount / chars.Length) + 1));
        return repeated[..Math.Min(repeated.Length, charCount)];
    }

    private static string GetRandomString(int length)
    {
        const string chars = "abcdefghijklmnopqrstuvwxyz0123456789";
        var random = new Random();
        return new string(Enumerable.Range(0, length).Select(_ => chars[random.Next(chars.Length)]).ToArray());
    }

    // ==================== Unit Tests: Configuration & Serialization ====================

    [Fact]
    public void StandaloneConfig_WithCompression_ShouldSerialize()
    {
        var compression = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Zstd,
            CompressionLevel: 3,
            MinCompressionSize: 64);

        var config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: compression);

        Assert.NotNull(config.Compression);
        Assert.True(config.Compression.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Compression.Backend);

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    [Fact]
    public void ClusterConfig_WithCompression_ShouldSerialize()
    {
        var compression = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Lz4,
            CompressionLevel: 0,
            MinCompressionSize: 128);

        var config = new GlideClusterClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: compression);

        Assert.NotNull(config.Compression);
        Assert.True(config.Compression.Enabled);
        Assert.Equal(CompressionBackend.Lz4, config.Compression.Backend);

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: true);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    [Fact]
    public void Config_WithoutCompression_ShouldSerialize()
    {
        var config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) });

        Assert.Null(config.Compression);

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    // ==================== Unit Tests: Protobuf Serialization ====================

    [Fact]
    public void SerializeCompressionConfig_Zstd_ShouldProduceValidProtobuf()
    {
        var compression = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Zstd,
            CompressionLevel: 3,
            MinCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(compression);

        Assert.True(protoConfig.Enabled);
        Assert.Equal(Protobuf.CompressionBackend.Zstd, protoConfig.Backend);
        Assert.Equal(3, protoConfig.CompressionLevel);
        Assert.Equal(64u, protoConfig.MinCompressionSize);
    }

    [Fact]
    public void SerializeCompressionConfig_Lz4_ShouldProduceValidProtobuf()
    {
        var compression = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Lz4,
            CompressionLevel: 0,
            MinCompressionSize: 128);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(compression);

        Assert.True(protoConfig.Enabled);
        Assert.Equal(Protobuf.CompressionBackend.Lz4, protoConfig.Backend);
        Assert.Equal(0, protoConfig.CompressionLevel);
        Assert.Equal(128u, protoConfig.MinCompressionSize);
    }

    [Fact]
    public void SerializeCompressionConfig_NullLevel_ShouldNotSetField()
    {
        var compression = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Zstd,
            CompressionLevel: null,
            MinCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(compression);

        Assert.Null(protoConfig.CompressionLevel);
    }

    // ==================== Unit Tests: Statistics ====================

    [Fact]
    public void Statistics_DefaultValues_ShouldBeZero()
    {
        var stats = new Statistics();

        Assert.Equal(0UL, stats.TotalValuesCompressed);
        Assert.Equal(0UL, stats.TotalValuesDecompressed);
        Assert.Equal(0UL, stats.TotalOriginalBytes);
        Assert.Equal(0UL, stats.TotalBytesCompressed);
        Assert.Equal(0UL, stats.TotalBytesDecompressed);
        Assert.Equal(0UL, stats.CompressionSkippedCount);
    }

    [Fact]
    public void Statistics_ToDictionary_ShouldContainAllKeys()
    {
        var stats = new Statistics
        {
            TotalConnections = 5,
            TotalClients = 2,
            TotalValuesCompressed = 100,
            TotalValuesDecompressed = 50,
            TotalOriginalBytes = 10000,
            TotalBytesCompressed = 5000,
            TotalBytesDecompressed = 10000,
            CompressionSkippedCount = 10,
        };

        var dict = stats.ToDictionary();

        Assert.Equal(10, dict.Count);
        Assert.Equal(5UL, dict["total_connections"]);
        Assert.Equal(2UL, dict["total_clients"]);
        Assert.Equal(100UL, dict["total_values_compressed"]);
        Assert.Equal(50UL, dict["total_values_decompressed"]);
        Assert.Equal(10000UL, dict["total_original_bytes"]);
        Assert.Equal(5000UL, dict["total_bytes_compressed"]);
        Assert.Equal(10000UL, dict["total_bytes_decompressed"]);
        Assert.Equal(10UL, dict["compression_skipped_count"]);
    }

    [Fact]
    public void Statistics_ToString_ShouldContainKeyFields()
    {
        var stats = new Statistics
        {
            TotalValuesCompressed = 42,
            TotalBytesCompressed = 1000,
            TotalBytesDecompressed = 2000,
        };

        var str = stats.ToString();
        Assert.Contains("42", str);
        Assert.Contains("1000", str);
        Assert.Contains("2000", str);
    }

    // ==================== Unit Tests: Data Generation Helpers ====================

    [Theory]
    [InlineData(512)]
    [InlineData(1024)]
    [InlineData(10240)]
    public void GenerateCompressibleText_ShouldReturnCorrectSize(int size)
    {
        var text = GenerateCompressibleText(size);
        Assert.Equal(size, text.Length);
    }

    [Theory]
    [InlineData(512)]
    [InlineData(1024)]
    public void GenerateJsonData_ShouldReturnCorrectSize(int size)
    {
        var text = GenerateJsonData(size);
        Assert.Equal(size, text.Length);
    }

    // ==================== Unit Tests: Backend Mismatch Config ====================

    [Fact]
    public void BackendMismatch_BothConfigsSerialize()
    {
        var zstdConfig = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: new CompressionConfiguration(
                Enabled: true,
                Backend: CompressionBackend.Zstd,
                CompressionLevel: 3,
                MinCompressionSize: 64));

        var lz4Config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: new CompressionConfiguration(
                Enabled: true,
                Backend: CompressionBackend.Lz4,
                CompressionLevel: 0,
                MinCompressionSize: 64));

        var zstdBytes = ConnectionRequestSerializer.Serialize(zstdConfig, clusterMode: false);
        var lz4Bytes = ConnectionRequestSerializer.Serialize(lz4Config, clusterMode: false);

        Assert.NotNull(zstdBytes);
        Assert.NotNull(lz4Bytes);
        Assert.NotEqual(zstdBytes, lz4Bytes);
    }

    // ==================== Unit Tests: Edge Cases ====================

    [Fact]
    public void DisabledCompression_ShouldSerialize()
    {
        var compression = new CompressionConfiguration(
            Enabled: false,
            Backend: CompressionBackend.Zstd,
            CompressionLevel: 3,
            MinCompressionSize: 64);

        Assert.False(compression.Enabled);

        var config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: compression);

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
    }

    [Fact]
    public void LargeMinCompressionSize_ShouldWork()
    {
        var config = new CompressionConfiguration(
            Enabled: true,
            MinCompressionSize: 1048576); // 1MB

        Assert.Equal(1048576u, config.MinCompressionSize);
    }

    [Fact]
    public void NegativeCompressionLevel_ShouldBeAccepted()
    {
        var config = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Zstd,
            CompressionLevel: -5);

        Assert.Equal(-5, config.CompressionLevel);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(config);
        Assert.Equal(-5, protoConfig.CompressionLevel);
    }

    // ==================== Unit Tests: Full ConnectionRequest Serialization ====================

    [Fact]
    public void FullConfig_WithAllFields_ShouldSerialize()
    {
        var config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379), new NodeAddress("localhost", 6380) },
            useTls: true,
            readFrom: ReadFrom.PreferReplica,
            credentials: new ServerCredentials("password", "user"),
            requestTimeout: 5000,
            clientName: "test-client",
            protocol: ProtocolVersion.Resp2,
            inflightRequestsLimit: 500,
            clientAz: "us-east-1a",
            reconnectStrategy: new BackoffStrategy(3, 100, 2, 10),
            databaseId: 1,
            lazyConnect: true,
            compression: new CompressionConfiguration(
                Enabled: true,
                Backend: CompressionBackend.Zstd,
                CompressionLevel: 3,
                MinCompressionSize: 64));

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    [Fact]
    public void ClusterFullConfig_WithCompression_ShouldSerialize()
    {
        var config = new GlideClusterClientConfiguration(
            addresses: new[] { new NodeAddress("node1", 6379), new NodeAddress("node2", 6379) },
            useTls: true,
            compression: new CompressionConfiguration(
                Enabled: true,
                Backend: CompressionBackend.Lz4,
                MinCompressionSize: 256));

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: true);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    // ==================== Unit Tests: Backend Level Validation ====================

    [Theory]
    [InlineData(1)]
    [InlineData(3)]
    [InlineData(10)]
    [InlineData(22)]
    [InlineData(-5)]
    public void ValidZstdLevels_ShouldCreateConfig(int level)
    {
        var config = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Zstd,
            CompressionLevel: level,
            MinCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(config);
        Assert.Equal(level, protoConfig.CompressionLevel);
    }

    [Theory]
    [InlineData(-128)]
    [InlineData(-10)]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(6)]
    [InlineData(12)]
    public void ValidLz4Levels_ShouldCreateConfig(int level)
    {
        var config = new CompressionConfiguration(
            Enabled: true,
            Backend: CompressionBackend.Lz4,
            CompressionLevel: level,
            MinCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(config);
        Assert.Equal(level, protoConfig.CompressionLevel);
    }

    // ==================================================================================
    // Integration Tests (require running Valkey/Redis server + FFI wiring)
    //
    // TODO: Enable these tests once GlideClient.CreateAsync, SetAsync, GetAsync,
    //       GetStatisticsAsync, and CloseAsync are wired through FFI to glide-core.
    //       These mirror the Python reference tests in:
    //         python/tests/async_tests/test_compression.py
    // ==================================================================================

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    public async Task Compression_SetGet_ShouldCompressLargeValues()
    {
        // Mirrors Python: test_compression_with_stats
        // 1. Create client with ZSTD compression (enabled=true, minCompressionSize=64)
        // 2. Capture initial stats: initial_compressed = stats.TotalValuesCompressed
        // 3. SET a 1KB compressible value (GenerateCompressibleText(1024))
        // 4. GET the value back, assert it matches original
        // 5. Capture stats after: assert stats.TotalValuesCompressed > initial_compressed
        // 6. Assert stats.TotalBytesCompressed < stats.TotalOriginalBytes
        await Task.CompletedTask; // placeholder
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetStatisticsAsync")]
    public async Task Compression_SmallValues_ShouldBeSkipped()
    {
        // Mirrors Python: test_compression_min_size_threshold_with_stats
        // 1. Create client with compression (minCompressionSize=64)
        // 2. Capture initial stats: initial_skipped, initial_compressed
        // 3. SET a 32-byte value (below threshold)
        // 4. Assert stats.CompressionSkippedCount > initial_skipped
        // 5. Assert stats.TotalValuesCompressed == initial_compressed (unchanged)
        // 6. SET a 128-byte value (above threshold)
        // 7. Assert stats.TotalValuesCompressed > initial_compressed
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetStatisticsAsync")]
    public async Task Compression_Disabled_ShouldNotCompress()
    {
        // Mirrors Python: test_disabled_compression_with_stats
        // 1. Create client WITHOUT compression
        // 2. Capture initial stats
        // 3. SET a 10KB value
        // 4. Assert stats.TotalValuesCompressed == initial (unchanged)
        // 5. Assert stats.CompressionSkippedCount == initial (unchanged)
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync")]
    public async Task Compression_BackendMismatch_ShouldReadTransparently()
    {
        // Mirrors Python: test_compression_backend_mismatch
        // 1. Create ZSTD client, SET a 1KB compressible value
        // 2. Create LZ4 client pointing to same server
        // 3. GET the value with LZ4 client — decompression detects backend from header
        // 4. Assert retrieved value matches original
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    public async Task Compression_BatchOperations_MsetMget()
    {
        // Mirrors Python: test_compression_batch_operations
        // 1. Create client with compression
        // 2. Capture initial stats
        // 3. MSET N keys with compressible values (each > minCompressionSize)
        // 4. MGET all keys, assert all values match
        // 5. Assert stats.TotalValuesCompressed increased by N
        // 6. Assert stats.TotalBytesCompressed < stats.TotalOriginalBytes
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    public async Task Compression_WithTTL_ShouldWork()
    {
        // Mirrors Python: test_compression_with_ttl
        // 1. Create client with compression
        // 2. SET a compressible value with TTL
        // 3. GET the value, assert it matches
        // 4. Assert stats.TotalValuesCompressed increased
        // 5. Wait for TTL expiry, assert GET returns null
        await Task.CompletedTask;
    }

    [Theory(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    [InlineData(CompressionBackend.Zstd, 1)]
    [InlineData(CompressionBackend.Zstd, 3)]
    [InlineData(CompressionBackend.Zstd, 10)]
    [InlineData(CompressionBackend.Lz4, 0)]
    [InlineData(CompressionBackend.Lz4, 6)]
    public async Task Compression_ValidLevels_ShouldCompressSuccessfully(
        CompressionBackend backend, int level)
    {
        // Mirrors Python: test_compression_levels
        // 1. Create client with specified backend and level
        // 2. SET a 1KB compressible value
        // 3. GET the value, assert it matches
        // 4. Assert stats.TotalValuesCompressed increased
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClusterClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    public async Task Compression_ClusterMultiSlot_ShouldCompressAcrossSlots()
    {
        // Mirrors Python: test_compression_cluster_multi_slot
        // 1. Create cluster client with compression
        // 2. SET N keys that hash to different slots
        // 3. GET all keys, assert values match
        // 4. Assert stats.TotalValuesCompressed increased by N
        await Task.CompletedTask;
    }

    [Theory(Skip = "Requires FFI wiring: GlideClient.CreateAsync")]
    [InlineData(CompressionBackend.Zstd, 100)]
    [InlineData(CompressionBackend.Lz4, 100)]
    public async Task Compression_InvalidLevel_ShouldFailAtClientCreation(
        CompressionBackend backend, int invalidLevel)
    {
        // Mirrors Python: test_invalid_compression_level
        // 1. Create config with an out-of-range compression level
        // 2. Attempt GlideClient.CreateAsync — should throw because Rust core rejects the level
        await Task.CompletedTask;
    }

    [Theory(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    [InlineData(512, "compressible")]
    [InlineData(1024, "compressible")]
    [InlineData(10240, "compressible")]
    [InlineData(512, "json")]
    [InlineData(1024, "json")]
    [InlineData(512, "base64")]
    [InlineData(1024, "unicode")]
    public async Task Compression_DataTypes_ShouldCompressAndRoundTrip(
        int size, string dataType)
    {
        // Mirrors Python: test_compression_data_types
        // 1. Create client with compression
        // 2. Generate data of the specified type and size
        // 3. SET the value, GET it back, assert round-trip equality
        // 4. Assert stats show compression was applied (for compressible data)
        //    or skipped (for incompressible data below ratio threshold)
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    public async Task Compression_MixedSizes_ShouldTrackSkipsAndCompressions()
    {
        // Mirrors Python: test_compression_mixed_sizes
        // 1. Create client with compression (minCompressionSize=64)
        // 2. SET values of varying sizes: some below threshold, some above
        // 3. Assert stats.CompressionSkippedCount increased for small values
        // 4. Assert stats.TotalValuesCompressed increased for large values
        // 5. Assert total skipped + compressed == total SET operations
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetStatisticsAsync")]
    public async Task Compression_EmptyValue_ShouldBeSkipped()
    {
        // Mirrors Python: test_compression_empty_and_edge_values
        // 1. Create client with compression
        // 2. SET an empty string value
        // 3. Assert stats.CompressionSkippedCount increased
        // 4. Assert stats.TotalValuesCompressed unchanged
        await Task.CompletedTask;
    }

    [Fact(Skip = "Requires FFI wiring: GlideClient.CreateAsync, SetAsync, GetAsync, GetStatisticsAsync")]
    public async Task Compression_LargeValue_10MB_ShouldCompress()
    {
        // Mirrors Python: test_compression_large_value
        // 1. Create client with compression
        // 2. SET a 10MB compressible value
        // 3. GET it back, assert round-trip equality
        // 4. Assert stats.TotalValuesCompressed increased
        // 5. Assert significant compression ratio (TotalBytesCompressed << TotalOriginalBytes)
        await Task.CompletedTask;
    }
}
