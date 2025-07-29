/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

/**
 * Enum representing the compression backend to use for automatic compression.
 */
public enum CompressionBackend {
    /**
     * Use zstd compression backend.
     *
     * <p>Zstandard (zstd) is a fast compression algorithm that provides good compression ratios.
     * It supports compression levels from 1 to 22, where higher levels provide better compression
     * but slower speed.
     */
    ZSTD,

    /**
     * Use lz4 compression backend.
     *
     * <p>LZ4 is an extremely fast compression algorithm that prioritizes speed over compression
     * ratio. It supports compression levels from 1 to 12, where higher levels provide better
     * compression but slower speed.
     */
    LZ4
}
