// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using System.Runtime.InteropServices;

namespace Valkey.Glide;

/// <summary>
/// Enum representing the compression backend to use for automatic compression.
/// </summary>
public enum CompressionBackend : uint
{
    /// <summary>
    /// Use zstd compression backend.
    /// 
    /// Zstandard (zstd) is a fast compression algorithm that provides good compression ratios.
    /// It supports compression levels from 1 to 22, where higher levels provide better compression
    /// but slower speed.
    /// </summary>
    Zstd = 0,

    /// <summary>
    /// Use lz4 compression backend.
    /// 
    /// LZ4 is an extremely fast compression algorithm that prioritizes speed over compression
    /// ratio. It supports compression levels from 1 to 12, where higher levels provide better
    /// compression but slower speed.
    /// </summary>
    Lz4 = 1,
}

/// <summary>
/// Configuration for automatic compression of values.
/// 
/// This configuration enables transparent compression and decompression of values for set-type
/// and get-type commands respectively. When enabled, values will be automatically compressed before
/// being sent to the server and decompressed when received from the server.
/// 
/// The compression is completely transparent to the application layer and maintains full backward
/// compatibility with existing data and non-compression clients.
/// 
/// Example usage:
/// <code>
/// var compressionConfig = new CompressionConfiguration
/// {
///     Enabled = true,
///     Backend = CompressionBackend.Zstd,
///     CompressionLevel = 3,
///     MinCompressionSize = 64,
///     MaxCompressionSize = 1024 * 1024 // 1MB
/// };
/// </code>
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public struct CompressionConfiguration
{
    /// <summary>
    /// Whether compression is enabled.
    /// Defaults to false.
    /// </summary>
    [MarshalAs(UnmanagedType.U1)]
    public bool Enabled;

    /// <summary>
    /// The compression backend to use.
    /// Defaults to CompressionBackend.Zstd.
    /// </summary>
    public CompressionBackend Backend;

    /// <summary>
    /// Whether a compression level is set.
    /// </summary>
    [MarshalAs(UnmanagedType.U1)]
    internal bool HasCompressionLevel;

    /// <summary>
    /// The compression level to use. If not set, the backend's default level will be used.
    /// 
    /// Valid ranges:
    /// - ZSTD: 1-22 (higher values provide better compression but slower speed)
    /// - LZ4: 1-12 (higher values provide better compression but slower speed)
    /// 
    /// Defaults to null (uses backend default).
    /// </summary>
    public uint CompressionLevel;

    /// <summary>
    /// The minimum size in bytes for values to be compressed.
    /// Values smaller than this will not be compressed to avoid overhead.
    /// Defaults to 64 bytes.
    /// </summary>
    public uint MinCompressionSize;

    /// <summary>
    /// Whether a maximum compression size is set.
    /// </summary>
    [MarshalAs(UnmanagedType.U1)]
    internal bool HasMaxCompressionSize;

    /// <summary>
    /// The maximum size in bytes for values to be compressed.
    /// Values larger than this will not be compressed.
    /// If not set, no maximum limit is applied.
    /// Defaults to null (no limit).
    /// </summary>
    public uint MaxCompressionSize;

    /// <summary>
    /// Creates a new CompressionConfiguration with default settings.
    /// </summary>
    /// <param name="enabled">Whether compression is enabled. Defaults to false.</param>
    /// <param name="backend">The compression backend to use. Defaults to CompressionBackend.Zstd.</param>
    /// <param name="compressionLevel">The compression level to use. If not set, the backend's default level will be used.</param>
    /// <param name="minCompressionSize">The minimum size in bytes for values to be compressed. Defaults to 64 bytes.</param>
    /// <param name="maxCompressionSize">The maximum size in bytes for values to be compressed. If not set, no maximum limit is applied.</param>
    public CompressionConfiguration(
        bool enabled = false,
        CompressionBackend backend = CompressionBackend.Zstd,
        uint? compressionLevel = null,
        uint minCompressionSize = 64,
        uint? maxCompressionSize = null)
    {
        Enabled = enabled;
        Backend = backend;
        HasCompressionLevel = compressionLevel.HasValue;
        CompressionLevel = compressionLevel ?? 0;
        MinCompressionSize = minCompressionSize;
        HasMaxCompressionSize = maxCompressionSize.HasValue;
        MaxCompressionSize = maxCompressionSize ?? 0;
    }

    /// <summary>
    /// Gets the compression level if set, otherwise null.
    /// </summary>
    public uint? GetCompressionLevel() => HasCompressionLevel ? CompressionLevel : null;

    /// <summary>
    /// Gets the maximum compression size if set, otherwise null.
    /// </summary>
    public uint? GetMaxCompressionSize() => HasMaxCompressionSize ? MaxCompressionSize : null;

    /// <summary>
    /// Validates the compression configuration parameters.
    /// </summary>
    /// <exception cref="ArgumentException">Thrown if any configuration parameter is invalid.</exception>
    public void Validate()
    {
        if (HasCompressionLevel)
        {
            // Validate compression level based on backend
            switch (Backend)
            {
                case CompressionBackend.Zstd:
                    if (CompressionLevel < 1 || CompressionLevel > 22)
                    {
                        throw new ArgumentException("CompressionLevel for ZSTD backend must be between 1 and 22");
                    }
                    break;
                case CompressionBackend.Lz4:
                    if (CompressionLevel < 1 || CompressionLevel > 12)
                    {
                        throw new ArgumentException("CompressionLevel for LZ4 backend must be between 1 and 12");
                    }
                    break;
                default:
                    throw new ArgumentException($"Unsupported compression backend: {Backend}");
            }
        }

        if (HasMaxCompressionSize && MaxCompressionSize < MinCompressionSize)
        {
            throw new ArgumentException("MaxCompressionSize must be greater than or equal to MinCompressionSize");
        }
    }
}

/// <summary>
/// Builder for CompressionConfiguration to provide a fluent API.
/// </summary>
public class CompressionConfigurationBuilder
{
    private bool _enabled = false;
    private CompressionBackend _backend = CompressionBackend.Zstd;
    private uint? _compressionLevel = null;
    private uint _minCompressionSize = 64;
    private uint? _maxCompressionSize = null;

    /// <summary>
    /// Sets whether compression is enabled.
    /// </summary>
    /// <param name="enabled">Whether compression is enabled.</param>
    /// <returns>This builder instance for method chaining.</returns>
    public CompressionConfigurationBuilder WithEnabled(bool enabled)
    {
        _enabled = enabled;
        return this;
    }

    /// <summary>
    /// Sets the compression backend to use.
    /// </summary>
    /// <param name="backend">The compression backend to use.</param>
    /// <returns>This builder instance for method chaining.</returns>
    public CompressionConfigurationBuilder WithBackend(CompressionBackend backend)
    {
        _backend = backend;
        return this;
    }

    /// <summary>
    /// Sets the compression level to use.
    /// If not set, the backend's default level will be used.
    /// 
    /// Valid ranges:
    /// - ZSTD: 1-22 (higher values provide better compression but slower speed)
    /// - LZ4: 1-12 (higher values provide better compression but slower speed)
    /// </summary>
    /// <param name="level">The compression level to use.</param>
    /// <returns>This builder instance for method chaining.</returns>
    public CompressionConfigurationBuilder WithCompressionLevel(uint level)
    {
        _compressionLevel = level;
        return this;
    }

    /// <summary>
    /// Sets the minimum size in bytes for values to be compressed.
    /// Values smaller than this will not be compressed to avoid overhead.
    /// </summary>
    /// <param name="size">The minimum size in bytes for values to be compressed.</param>
    /// <returns>This builder instance for method chaining.</returns>
    public CompressionConfigurationBuilder WithMinCompressionSize(uint size)
    {
        _minCompressionSize = size;
        return this;
    }

    /// <summary>
    /// Sets the maximum size in bytes for values to be compressed.
    /// Values larger than this will not be compressed.
    /// If not set, no maximum limit is applied.
    /// </summary>
    /// <param name="size">The maximum size in bytes for values to be compressed.</param>
    /// <returns>This builder instance for method chaining.</returns>
    public CompressionConfigurationBuilder WithMaxCompressionSize(uint size)
    {
        _maxCompressionSize = size;
        return this;
    }

    /// <summary>
    /// Builds and validates the compression configuration.
    /// </summary>
    /// <returns>A validated CompressionConfiguration instance.</returns>
    /// <exception cref="ArgumentException">Thrown if any configuration parameter is invalid.</exception>
    public CompressionConfiguration Build()
    {
        var config = new CompressionConfiguration(
            _enabled,
            _backend,
            _compressionLevel,
            _minCompressionSize,
            _maxCompressionSize);

        config.Validate();
        return config;
    }
}
