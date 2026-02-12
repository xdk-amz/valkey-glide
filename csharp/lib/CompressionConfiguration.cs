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
///
/// This is a record type providing structural equality, making it easy to compare
/// configurations in tests and application code.
/// </remarks>
/// <param name="Enabled">Whether compression is enabled.</param>
/// <param name="Backend">The compression backend to use. Defaults to <see cref="CompressionBackend.Zstd"/>.</param>
/// <param name="CompressionLevel">The compression level. If null, the backend default is used.
/// Valid ranges are backend-specific and validated by the Rust core.
/// ZSTD default is 3, LZ4 default is 0.</param>
/// <param name="MinCompressionSize">Minimum value size in bytes for compression. Defaults to 64.
/// Must be at least <see cref="MinCompressedSize"/> (6 bytes).</param>
/// <exception cref="ConfigurationError">Thrown when configuration parameters are invalid.</exception>
public record CompressionConfiguration(
    bool Enabled = false,
    CompressionBackend Backend = CompressionBackend.Zstd,
    int? CompressionLevel = null,
    uint MinCompressionSize = 64)
{
    /// <summary>
    /// Minimum allowed value for <see cref="MinCompressionSize"/>.
    /// This is the header size (5 bytes) + 1 byte of data = 6 bytes.
    /// </summary>
    /// <remarks>
    /// IMPORTANT: This must stay in sync with the Rust core constant <c>MIN_COMPRESSED_SIZE</c>
    /// defined in glide-core/src/compression.rs. If the header format changes in the Rust core,
    /// this value must be updated to match. Once FFI is fully wired, consider reading this
    /// value from the native library instead of hardcoding it.
    /// </remarks>
    public const uint MinCompressedSize = 6;

    // Validate on construction. Record primary constructors don't support throwing,
    // so we validate in the init block via a property trick isn't available — instead
    // we validate here and the compiler calls this after setting all properties.
    private bool _validated = Validate(Enabled, Backend, CompressionLevel, MinCompressionSize);

    private static bool Validate(bool enabled, CompressionBackend backend, int? compressionLevel, uint minCompressionSize)
    {
        if (minCompressionSize < MinCompressedSize)
        {
            // Note: error message uses snake_case intentionally for cross-language consistency
            // with Python and Java bindings (see python/glide-shared/glide_shared/config.py).
            throw new ConfigurationError(
                $"min_compression_size should be at least {MinCompressedSize} bytes");
        }

        if (!Enum.IsDefined(typeof(CompressionBackend), backend))
        {
            throw new ConfigurationError(
                $"Invalid compression Backend: {backend}");
        }

        // Note: compression_level validation is performed by the Rust core,
        // which uses the actual compression library's valid ranges.
        // This ensures the validation stays in sync with library updates.

        return true;
    }
}
