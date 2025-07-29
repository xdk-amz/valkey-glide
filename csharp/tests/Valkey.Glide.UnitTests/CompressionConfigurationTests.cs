// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using Xunit;

namespace Valkey.Glide.UnitTests;

public class CompressionConfigurationTests
{
    [Fact]
    public void TestDefaultConfiguration()
    {
        var config = new CompressionConfiguration();

        Assert.False(config.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Backend);
        Assert.Null(config.GetCompressionLevel());
        Assert.Equal(64u, config.MinCompressionSize);
        Assert.Null(config.GetMaxCompressionSize());
    }

    [Fact]
    public void TestEnabledConfiguration()
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: 6,
            minCompressionSize: 128,
            maxCompressionSize: 1024);

        Assert.True(config.Enabled);
        Assert.Equal(CompressionBackend.Lz4, config.Backend);
        Assert.Equal(6u, config.GetCompressionLevel());
        Assert.Equal(128u, config.MinCompressionSize);
        Assert.Equal(1024u, config.GetMaxCompressionSize());
    }

    [Fact]
    public void TestValidZstdCompressionLevel()
    {
        // Test valid ZSTD compression levels (1-22)
        var config1 = new CompressionConfiguration(backend: CompressionBackend.Zstd, compressionLevel: 1);
        Assert.DoesNotThrow(config1.Validate);

        var config22 = new CompressionConfiguration(backend: CompressionBackend.Zstd, compressionLevel: 22);
        Assert.DoesNotThrow(config22.Validate);

        var config10 = new CompressionConfiguration(backend: CompressionBackend.Zstd, compressionLevel: 10);
        Assert.DoesNotThrow(config10.Validate);
    }

    [Fact]
    public void TestInvalidZstdCompressionLevel()
    {
        // Test invalid ZSTD compression levels
        var config0 = new CompressionConfiguration(backend: CompressionBackend.Zstd, compressionLevel: 0);
        var exception1 = Assert.Throws<ArgumentException>(config0.Validate);
        Assert.Contains("CompressionLevel for ZSTD backend must be between 1 and 22", exception1.Message);

        var config23 = new CompressionConfiguration(backend: CompressionBackend.Zstd, compressionLevel: 23);
        var exception2 = Assert.Throws<ArgumentException>(config23.Validate);
        Assert.Contains("CompressionLevel for ZSTD backend must be between 1 and 22", exception2.Message);
    }

    [Fact]
    public void TestValidLz4CompressionLevel()
    {
        // Test valid LZ4 compression levels (1-12)
        var config1 = new CompressionConfiguration(backend: CompressionBackend.Lz4, compressionLevel: 1);
        Assert.DoesNotThrow(config1.Validate);

        var config12 = new CompressionConfiguration(backend: CompressionBackend.Lz4, compressionLevel: 12);
        Assert.DoesNotThrow(config12.Validate);

        var config6 = new CompressionConfiguration(backend: CompressionBackend.Lz4, compressionLevel: 6);
        Assert.DoesNotThrow(config6.Validate);
    }

    [Fact]
    public void TestInvalidLz4CompressionLevel()
    {
        // Test invalid LZ4 compression levels
        var config0 = new CompressionConfiguration(backend: CompressionBackend.Lz4, compressionLevel: 0);
        var exception1 = Assert.Throws<ArgumentException>(config0.Validate);
        Assert.Contains("CompressionLevel for LZ4 backend must be between 1 and 12", exception1.Message);

        var config13 = new CompressionConfiguration(backend: CompressionBackend.Lz4, compressionLevel: 13);
        var exception2 = Assert.Throws<ArgumentException>(config13.Validate);
        Assert.Contains("CompressionLevel for LZ4 backend must be between 1 and 12", exception2.Message);
    }

    [Fact]
    public void TestInvalidMaxCompressionSize()
    {
        // Test maxCompressionSize < minCompressionSize
        var config = new CompressionConfiguration(
            minCompressionSize: 128,
            maxCompressionSize: 64);

        var exception = Assert.Throws<ArgumentException>(config.Validate);
        Assert.Contains("MaxCompressionSize must be greater than or equal to MinCompressionSize", exception.Message);
    }

    [Fact]
    public void TestValidMaxCompressionSize()
    {
        var config1 = new CompressionConfiguration(minCompressionSize: 64, maxCompressionSize: 128);
        Assert.DoesNotThrow(config1.Validate);

        var config2 = new CompressionConfiguration(minCompressionSize: 0, maxCompressionSize: 0);
        Assert.DoesNotThrow(config2.Validate);

        var config3 = new CompressionConfiguration(minCompressionSize: 100, maxCompressionSize: 100);
        Assert.DoesNotThrow(config3.Validate);
    }

    [Fact]
    public void TestNullCompressionLevel()
    {
        // Test that null compression level is valid (uses backend default)
        var configZstd = new CompressionConfiguration(backend: CompressionBackend.Zstd);
        Assert.DoesNotThrow(configZstd.Validate);
        Assert.Null(configZstd.GetCompressionLevel());

        var configLz4 = new CompressionConfiguration(backend: CompressionBackend.Lz4);
        Assert.DoesNotThrow(configLz4.Validate);
        Assert.Null(configLz4.GetCompressionLevel());
    }

    [Fact]
    public void TestNullMaxCompressionSize()
    {
        // Test that null maxCompressionSize is valid (no limit)
        var config = new CompressionConfiguration(minCompressionSize: 64);
        Assert.DoesNotThrow(config.Validate);
        Assert.Null(config.GetMaxCompressionSize());
    }

    [Fact]
    public void TestComplexValidConfiguration()
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: 15,
            minCompressionSize: 32,
            maxCompressionSize: 2048);

        Assert.DoesNotThrow(config.Validate);
        Assert.True(config.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Backend);
        Assert.Equal(15u, config.GetCompressionLevel());
        Assert.Equal(32u, config.MinCompressionSize);
        Assert.Equal(2048u, config.GetMaxCompressionSize());
    }
}

public class CompressionConfigurationBuilderTests
{
    [Fact]
    public void TestBuilderDefaultConfiguration()
    {
        var config = new CompressionConfigurationBuilder().Build();

        Assert.False(config.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Backend);
        Assert.Null(config.GetCompressionLevel());
        Assert.Equal(64u, config.MinCompressionSize);
        Assert.Null(config.GetMaxCompressionSize());
    }

    [Fact]
    public void TestBuilderEnabledConfiguration()
    {
        var config = new CompressionConfigurationBuilder()
            .WithEnabled(true)
            .WithBackend(CompressionBackend.Lz4)
            .WithCompressionLevel(6)
            .WithMinCompressionSize(128)
            .WithMaxCompressionSize(1024)
            .Build();

        Assert.True(config.Enabled);
        Assert.Equal(CompressionBackend.Lz4, config.Backend);
        Assert.Equal(6u, config.GetCompressionLevel());
        Assert.Equal(128u, config.MinCompressionSize);
        Assert.Equal(1024u, config.GetMaxCompressionSize());
    }

    [Fact]
    public void TestBuilderValidatesConfiguration()
    {
        var builder = new CompressionConfigurationBuilder()
            .WithBackend(CompressionBackend.Zstd)
            .WithCompressionLevel(25); // Invalid level for ZSTD

        var exception = Assert.Throws<ArgumentException>(() => builder.Build());
        Assert.Contains("CompressionLevel for ZSTD backend must be between 1 and 22", exception.Message);
    }

    [Fact]
    public void TestBuilderMethodChaining()
    {
        var config = new CompressionConfigurationBuilder()
            .WithEnabled(true)
            .WithBackend(CompressionBackend.Zstd)
            .WithCompressionLevel(10)
            .WithMinCompressionSize(32)
            .WithMaxCompressionSize(2048)
            .Build();

        Assert.True(config.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Backend);
        Assert.Equal(10u, config.GetCompressionLevel());
        Assert.Equal(32u, config.MinCompressionSize);
        Assert.Equal(2048u, config.GetMaxCompressionSize());
    }
}

public class ConnectionConfigurationCompressionTests
{
    [Fact]
    public void TestStandaloneClientConfigurationWithCompression()
    {
        var compressionConfig = new CompressionConfiguration(enabled: true, backend: CompressionBackend.Zstd);
        var clientConfig = new StandaloneClientConfigurationBuilder()
            .WithAddress("localhost", 6379)
            .WithCompression(compressionConfig)
            .Build();

        Assert.NotNull(clientConfig.Request.Compression);
        Assert.True(clientConfig.Request.Compression.Value.Enabled);
        Assert.Equal(CompressionBackend.Zstd, clientConfig.Request.Compression.Value.Backend);
    }

    [Fact]
    public void TestClusterClientConfigurationWithCompression()
    {
        var compressionConfig = new CompressionConfiguration(enabled: true, backend: CompressionBackend.Lz4);
        var clusterConfig = new ClusterClientConfigurationBuilder()
            .WithAddress("localhost", 6379)
            .WithCompression(compressionConfig)
            .Build();

        Assert.NotNull(clusterConfig.Request.Compression);
        Assert.True(clusterConfig.Request.Compression.Value.Enabled);
        Assert.Equal(CompressionBackend.Lz4, clusterConfig.Request.Compression.Value.Backend);
    }

    [Fact]
    public void TestStandaloneClientConfigurationWithInvalidCompression()
    {
        var compressionConfig = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: 25); // Invalid level for ZSTD

        var builder = new StandaloneClientConfigurationBuilder()
            .WithAddress("localhost", 6379);

        var exception = Assert.Throws<ArgumentException>(() => builder.WithCompression(compressionConfig));
        Assert.Contains("CompressionLevel for ZSTD backend must be between 1 and 22", exception.Message);
    }

    [Fact]
    public void TestClusterClientConfigurationWithInvalidCompression()
    {
        var compressionConfig = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: 15); // Invalid level for LZ4

        var builder = new ClusterClientConfigurationBuilder()
            .WithAddress("localhost", 6379);

        var exception = Assert.Throws<ArgumentException>(() => builder.WithCompression(compressionConfig));
        Assert.Contains("CompressionLevel for LZ4 backend must be between 1 and 12", exception.Message);
    }

    [Fact]
    public void TestStandaloneClientConfigurationConstructorWithCompression()
    {
        var compressionConfig = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: 10);

        var clientConfig = new StandaloneClientConfiguration(
            addresses: [("localhost", 6379)],
            compression: compressionConfig);

        Assert.NotNull(clientConfig.Request.Compression);
        Assert.True(clientConfig.Request.Compression.Value.Enabled);
        Assert.Equal(CompressionBackend.Zstd, clientConfig.Request.Compression.Value.Backend);
        Assert.Equal(10u, clientConfig.Request.Compression.Value.GetCompressionLevel());
    }

    [Fact]
    public void TestClusterClientConfigurationConstructorWithCompression()
    {
        var compressionConfig = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: 6);

        var clusterConfig = new ClusterClientConfiguration(
            addresses: [("localhost", 6379)],
            compression: compressionConfig);

        Assert.NotNull(clusterConfig.Request.Compression);
        Assert.True(clusterConfig.Request.Compression.Value.Enabled);
        Assert.Equal(CompressionBackend.Lz4, clusterConfig.Request.Compression.Value.Backend);
        Assert.Equal(6u, clusterConfig.Request.Compression.Value.GetCompressionLevel());
    }
}
