// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Represents the compression configuration for automatic compression of values.
/// </summary>
/// <remarks>
/// When compression is enabled, values that meet the minimum size threshold will be
/// automatically compressed before being sent to the server and decompressed when retrieved.
/// Compression is transparent to the user — compressed and uncompressed clients can
/// interoperate seamlessly.
/// </remarks>
public class CompressionConfiguration
{
    /// <summary>
    /// Minimum allowed value for <see cref="MinCompressionSize"/>.
    /// This is the header size (5 bytes) + 1 byte of data = 6 bytes.
    /// Matches the Rust core constant <c>MIN_COMPRESSED_SIZE</c>.
    /// </summary>
    public const uint MinCompressedSize = 6;

    /// <summary>
    /// Whether compression is enabled.
    /// </summary>
    public bool Enabled { get; }

    /// <summary>
    /// The compression backend to use.
    /// </summary>
    public CompressionBackend Backend { get; }

    /// <summary>
    /// The compression level to use. If null, the backend's default level will be used.
    /// Valid ranges are backend-specific and validated by the Rust core.
    /// ZSTD default is 3, LZ4 default is 0.
    /// </summary>
    public int? CompressionLevel { get; }

    /// <summary>
    /// The minimum size in bytes for values to be compressed.
    /// Values smaller than this will not be compressed. Defaults to 64 bytes.
    /// Must be at least <see cref="MinCompressedSize"/> (6 bytes).
    /// </summary>
    public uint MinCompressionSize { get; }

    /// <summary>
    /// Creates a new compression configuration.
    /// </summary>
    /// <param name="enabled">Whether compression is enabled.</param>
    /// <param name="backend">The compression backend to use. Defaults to <see cref="CompressionBackend.Zstd"/>.</param>
    /// <param name="compressionLevel">The compression level. If null, the backend default is used.</param>
    /// <param name="minCompressionSize">Minimum value size in bytes for compression. Defaults to 64.</param>
    /// <exception cref="ConfigurationError">Thrown when configuration parameters are invalid.</exception>
    public CompressionConfiguration(
        bool enabled = false,
        CompressionBackend backend = CompressionBackend.Zstd,
        int? compressionLevel = null,
        uint minCompressionSize = 64)
    {
        Enabled = enabled;
        Backend = backend;
        CompressionLevel = compressionLevel;
        MinCompressionSize = minCompressionSize;

        Validate();
    }

    /// <summary>
    /// Validates the compression configuration parameters.
    /// </summary>
    /// <exception cref="ConfigurationError">Thrown when configuration parameters are invalid.</exception>
    private void Validate()
    {
        if (MinCompressionSize < MinCompressedSize)
        {
            throw new ConfigurationError(
                $"min_compression_size should be at least {MinCompressedSize} bytes");
        }

        if (!Enum.IsDefined(typeof(CompressionBackend), Backend))
        {
            throw new ConfigurationError(
                $"Invalid compression backend: {Backend}");
        }

        // Note: compression_level validation is performed by the Rust core,
        // which uses the actual compression library's valid ranges.
        // This ensures the validation stays in sync with library updates.
    }
}
