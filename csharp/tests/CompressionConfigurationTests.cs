// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using Glide;
using Xunit;

namespace Glide.Tests;

/// <summary>
/// Unit tests for CompressionConfiguration validation.
/// </summary>
public class CompressionConfigurationTests
{
    [Fact]
    public void DefaultConfiguration_ShouldHaveCorrectDefaults()
    {
        var config = new CompressionConfiguration();

        Assert.False(config.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Backend);
        Assert.Null(config.CompressionLevel);
        Assert.Equal(64u, config.MinCompressionSize);
    }

    [Fact]
    public void EnabledWithZstd_ShouldCreateSuccessfully()
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: 3,
            minCompressionSize: 64);

        Assert.True(config.Enabled);
        Assert.Equal(CompressionBackend.Zstd, config.Backend);
        Assert.Equal(3, config.CompressionLevel);
        Assert.Equal(64u, config.MinCompressionSize);
    }

    [Fact]
    public void EnabledWithLz4_ShouldCreateSuccessfully()
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: 0,
            minCompressionSize: 128);

        Assert.True(config.Enabled);
        Assert.Equal(CompressionBackend.Lz4, config.Backend);
        Assert.Equal(0, config.CompressionLevel);
        Assert.Equal(128u, config.MinCompressionSize);
    }

    [Fact]
    public void NullCompressionLevel_ShouldUseBackendDefault()
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd);

        Assert.Null(config.CompressionLevel);
    }

    [Fact]
    public void MinCompressionSize_AtMinimum_ShouldSucceed()
    {
        // MIN_COMPRESSED_SIZE = 6 (HEADER_SIZE + 1)
        var config = new CompressionConfiguration(
            enabled: true,
            minCompressionSize: CompressionConfiguration.MinCompressedSize);

        Assert.Equal(CompressionConfiguration.MinCompressedSize, config.MinCompressionSize);
    }

    [Fact]
    public void MinCompressionSize_BelowMinimum_ShouldThrowConfigurationError()
    {
        var ex = Assert.Throws<ConfigurationError>(() =>
            new CompressionConfiguration(
                enabled: true,
                minCompressionSize: CompressionConfiguration.MinCompressedSize - 1));

        Assert.Contains("min_compression_size", ex.Message);
        Assert.Contains($"{CompressionConfiguration.MinCompressedSize}", ex.Message);
    }

    [Fact]
    public void MinCompressionSize_Zero_ShouldThrowConfigurationError()
    {
        var ex = Assert.Throws<ConfigurationError>(() =>
            new CompressionConfiguration(
                enabled: true,
                minCompressionSize: 0));

        Assert.Contains("min_compression_size", ex.Message);
    }

    [Theory]
    [InlineData(1u)]
    [InlineData(2u)]
    [InlineData(3u)]
    [InlineData(4u)]
    [InlineData(5u)]
    public void MinCompressionSize_BelowMinCompressedSize_ShouldThrow(uint size)
    {
        Assert.Throws<ConfigurationError>(() =>
            new CompressionConfiguration(
                enabled: true,
                minCompressionSize: size));
    }

    [Theory]
    [InlineData(6u)]   // MinCompressedSize exactly
    [InlineData(7u)]
    [InlineData(64u)]  // Default
    [InlineData(128u)]
    [InlineData(1024u)]
    [InlineData(1048576u)] // 1MB
    public void MinCompressionSize_ValidValues_ShouldSucceed(uint size)
    {
        var config = new CompressionConfiguration(
            enabled: true,
            minCompressionSize: size);

        Assert.Equal(size, config.MinCompressionSize);
    }

    [Fact]
    public void MinCompressedSize_ConstantIs6()
    {
        // HEADER_SIZE (5) + 1 = 6
        Assert.Equal(6u, CompressionConfiguration.MinCompressedSize);
    }

    [Theory]
    [InlineData(CompressionBackend.Zstd)]
    [InlineData(CompressionBackend.Lz4)]
    public void ValidBackends_ShouldCreateSuccessfully(CompressionBackend backend)
    {
        var config = new CompressionConfiguration(
            enabled: true,
            backend: backend);

        Assert.Equal(backend, config.Backend);
    }

    [Fact]
    public void InvalidBackend_ShouldThrowConfigurationError()
    {
        Assert.Throws<ConfigurationError>(() =>
            new CompressionConfiguration(
                enabled: true,
                backend: (CompressionBackend)99));
    }

    [Theory]
    [InlineData(-5)]   // Negative ZSTD level
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(3)]    // ZSTD default
    [InlineData(10)]
    [InlineData(22)]   // ZSTD max
    public void ZstdCompressionLevels_ShouldAcceptAnyInt(int level)
    {
        // Note: actual level validation is done by Rust core at client creation time
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Zstd,
            compressionLevel: level);

        Assert.Equal(level, config.CompressionLevel);
    }

    [Theory]
    [InlineData(-128)]
    [InlineData(-10)]
    [InlineData(0)]    // LZ4 default
    [InlineData(1)]
    [InlineData(6)]
    [InlineData(12)]   // LZ4 max
    public void Lz4CompressionLevels_ShouldAcceptAnyInt(int level)
    {
        // Note: actual level validation is done by Rust core at client creation time
        var config = new CompressionConfiguration(
            enabled: true,
            backend: CompressionBackend.Lz4,
            compressionLevel: level);

        Assert.Equal(level, config.CompressionLevel);
    }
}
