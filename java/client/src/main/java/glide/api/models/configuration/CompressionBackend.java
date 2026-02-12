/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

/**
 * Represents the compression backend to use for automatic compression.
 *
 * @see CompressionConfiguration
 */
public enum CompressionBackend {
    /** Use zstd compression backend. Default compression level is 3. */
    ZSTD,
    /** Use lz4 compression backend. Default compression level is 0. */
    LZ4
}
