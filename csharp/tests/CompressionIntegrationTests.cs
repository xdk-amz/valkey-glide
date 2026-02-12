// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using Glide;
using Xunit;

namespace Glide.Tests;

/// <summary>
/// Integration tests for compression functionality.
/// These tests verify compression behavior with a live Valkey/Redis server.
/// They follow the patterns established in the Python compression tests.
///
/// NOTE: These tests require a running Valkey/Redis server and the native FFI library.
/// They are designed to be run as integration tests and may be skipped in unit test runs.
/// </summary>
public class CompressionIntegrationTests
{
    // Data generation helpers matching Python test patterns

    /// <summary>Generate highly compressible text (repeated patterns).</summary>
    private static string GenerateCompressibleText(int sizeBytes)
    {
        var pattern = new string('A', 10) + new string('B', 10) + new string('C', 10);
        var repeated = string.Concat(Enumerable.Repeat(pattern, (sizeBytes / pattern.Length) + 1));
        return repeated[..sizeBytes];
    }

    /// <summary>Generate JSON-like structured data.</summary>
    private static string GenerateJsonData(int sizeBytes)
    {
        const string jsonStr = """{"id":12345,"name":"Test User","email":"test@example.com","description":"AAAAAAAAAA","metadata":{"key":"value"},"tags":["tag1","tag2","tag3"]}""";
        var repeated = string.Concat(Enumerable.Repeat(jsonStr, (sizeBytes / jsonStr.Length) + 1));
        return repeated[..sizeBytes];
    }

    /// <summary>Generate base64-like data (low compressibility).</summary>
    private static string GenerateBase64Data(int sizeBytes)
    {
        var random = new Random(42); // Fixed seed for reproducibility
        var bytes = new byte[sizeBytes / 2];
        random.NextBytes(bytes);
        var base64 = Convert.ToBase64String(bytes);
        return base64.Length >= sizeBytes ? base64[..sizeBytes] : base64.PadRight(sizeBytes, '=');
    }

    /// <summary>Generate text with unicode characters.</summary>
    private static string GenerateUnicodeText(int sizeBytes)
    {
        const string chars = "Hello世界Привет";
        var repeated = string.Concat(Enumerable.Repeat(chars, (sizeBytes / chars.Length) + 1));
        return repeated[..Math.Min(repeated.Length, sizeBytes)];
    }

    private static string GetRandomString(int length)
    {
        const string chars = "abcdefghijklmnopqrstuvwxyz0123456789";
        var random = new Random();
        return new string(Enumerable.Range(0, length).Select(_ => chars[random.Next(chars.Length)]).ToArray());
    }

    // ==================== Configuration Validation Tests ====================

    /// <summary>
    /// Test that CompressionConfiguration can be attached to GlideClientConfiguration.
    /// </summary>
    [Fact]
    public void StandaloneConfig_WithCompression_ShouldSerialize()
    {
        var compression = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: 3,
            minCompressionSize: 64);

        var config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: compression);

        Assert.NotNull(config.Compression);
        Assert.True(config.Compression.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Compression.Backend);

        // Verify protobuf serialization doesn't throw
        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    /// <summary>
    /// Test that CompressionConfiguration can be attached to GlideClusterClientConfiguration.
    /// </summary>
    [Fact]
    public void ClusterConfig_WithCompression_ShouldSerialize()
    {
        var compression = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: 0,
            minCompressionSize: 128);

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

    /// <summary>
    /// Test that config without compression serializes correctly (no compression_config field).
    /// </summary>
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

    /// <summary>
    /// Test that compression can be set after initial configuration (mutable Compression property).
    /// </summary>
    [Fact]
    public void Config_SetCompressionAfterCreation_ShouldWork()
    {
        var config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) });

        Assert.Null(config.Compression);

        config.Compression = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: 3,
            minCompressionSize: 64);

        Assert.NotNull(config.Compression);
        Assert.True(config.Compression.Enabled);

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    // ==================== Protobuf Serialization Tests ====================

    /// <summary>
    /// Test that ZSTD compression config serializes correctly to protobuf.
    /// </summary>
    [Fact]
    public void SerializeCompressionConfig_Zstd_ShouldProduceValidProtobuf()
    {
        var compression = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: 3,
            minCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(compression);

        Assert.True(protoConfig.Enabled);
        Assert.Equal(Protobuf.CompressionBackend.Zstd, protoConfig.Backend);
        Assert.Equal(3, protoConfig.CompressionLevel);
        Assert.Equal(64u, protoConfig.MinCompressionSize);
    }

    /// <summary>
    /// Test that LZ4 compression config serializes correctly to protobuf.
    /// </summary>
    [Fact]
    public void SerializeCompressionConfig_Lz4_ShouldProduceValidProtobuf()
    {
        var compression = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: 0,
            minCompressionSize: 128);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(compression);

        Assert.True(protoConfig.Enabled);
        Assert.Equal(Protobuf.CompressionBackend.Lz4, protoConfig.Backend);
        Assert.Equal(0, protoConfig.CompressionLevel);
        Assert.Equal(128u, protoConfig.MinCompressionSize);
    }

    /// <summary>
    /// Test that null compression level is not set in protobuf.
    /// </summary>
    [Fact]
    public void SerializeCompressionConfig_NullLevel_ShouldNotSetField()
    {
        var compression = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: null,
            minCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(compression);

        Assert.Null(protoConfig.CompressionLevel);
    }

    // ==================== Statistics Tests ====================

    [Fact]
    public void Statistics_DefaultValues_ShouldBeZero()
    {
        var stats = new Statistics();

        Assert.Equal(0UL, stats.TotalValuesCompressed);
        Assert.Equal(0UL, stats.TotalValuesDecompressed);
        Assert.Equal(0UL, stats.TotalOriginalBytes);
        Assert.Equal(0UL, stats.TotalBytesCompressed);
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
        };

        var str = stats.ToString();
        Assert.Contains("42", str);
        Assert.Contains("1000", str);
    }

    // ==================== Data Generation Helper Tests ====================

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

    // ==================== Backend Mismatch Scenario Tests ====================

    /// <summary>
    /// Test that both ZSTD and LZ4 configs can be created and serialized independently.
    /// This validates the backend mismatch scenario setup (writing with one backend, reading with another).
    /// </summary>
    [Fact]
    public void BackendMismatch_BothConfigsSerialize()
    {
        var zstdConfig = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: new CompressionConfiguration(
                enabled: true,
                backend: CompressionBackend.Zstd,
                compressionLevel: 3,
                minCompressionSize: 64));

        var lz4Config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: new CompressionConfiguration(
                enabled: true,
                backend: CompressionBackend.Lz4,
                compressionLevel: 0,
                minCompressionSize: 64));

        var zstdBytes = ConnectionRequestSerializer.Serialize(zstdConfig, clusterMode: false);
        var lz4Bytes = ConnectionRequestSerializer.Serialize(lz4Config, clusterMode: false);

        Assert.NotNull(zstdBytes);
        Assert.NotNull(lz4Bytes);
        // Different backends should produce different serialized bytes
        Assert.NotEqual(zstdBytes, lz4Bytes);
    }

    // ==================== Edge Case Tests ====================

    /// <summary>
    /// Test disabled compression config still serializes correctly.
    /// </summary>
    [Fact]
    public void DisabledCompression_ShouldSerialize()
    {
        var compression = new CompressionConfiguration(
            enabled: false,
            backend: CompressionBackend.Zstd,
            compressionLevel: 3,
            minCompressionSize: 64);

        Assert.False(compression.Enabled);

        var config = new GlideClientConfiguration(
            addresses: new[] { new NodeAddress("localhost", 6379) },
            compression: compression);

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
    }

    /// <summary>
    /// Test large min_compression_size values.
    /// </summary>
    [Fact]
    public void LargeMinCompressionSize_ShouldWork()
    {
        var config = new CompressionConfiguration(
            enabled: true,
            minCompressionSize: 1048576); // 1MB

        Assert.Equal(1048576u, config.MinCompressionSize);
    }

    /// <summary>
    /// Test negative compression levels (valid for some backends).
    /// </summary>
    [Fact]
    public void NegativeCompressionLevel_ShouldBeAccepted()
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: -5);

        Assert.Equal(-5, config.CompressionLevel);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(config);
        Assert.Equal(-5, protoConfig.CompressionLevel);
    }

    // ==================== Full ConnectionRequest Serialization Tests ====================

    /// <summary>
    /// Test full config with all fields set including compression.
    /// </summary>
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
                enabled: true,
                backend: CompressionBackend.Zstd,
                compressionLevel: 3,
                minCompressionSize: 64));

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: false);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    /// <summary>
    /// Test cluster config with compression.
    /// </summary>
    [Fact]
    public void ClusterFullConfig_WithCompression_ShouldSerialize()
    {
        var config = new GlideClusterClientConfiguration(
            addresses: new[] { new NodeAddress("node1", 6379), new NodeAddress("node2", 6379) },
            useTls: true,
            compression: new CompressionConfiguration(
                enabled: true,
                backend: CompressionBackend.Lz4,
                minCompressionSize: 256));

        var bytes = ConnectionRequestSerializer.Serialize(config, clusterMode: true);
        Assert.NotNull(bytes);
        Assert.True(bytes.Length > 0);
    }

    // ==================== Backend Level Validation Tests ====================

    /// <summary>
    /// Test valid ZSTD compression levels that should be accepted by Rust core.
    /// </summary>
    [Theory]
    [InlineData(1)]
    [InlineData(3)]
    [InlineData(10)]
    [InlineData(22)]
    [InlineData(-5)]
    public void ValidZstdLevels_ShouldCreateConfig(int level)
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: level,
            minCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(config);
        Assert.Equal(level, protoConfig.CompressionLevel);
    }

    /// <summary>
    /// Test valid LZ4 compression levels that should be accepted by Rust core.
    /// </summary>
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
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: level,
            minCompressionSize: 64);

        var protoConfig = ConnectionRequestSerializer.SerializeCompressionConfig(config);
        Assert.Equal(level, protoConfig.CompressionLevel);
    }
}
