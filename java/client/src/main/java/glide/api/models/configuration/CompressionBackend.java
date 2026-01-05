/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

/**
 * Represents the compression backend to use for automatic compression.
 *
 * <p>Compression is applied automatically to values in SET-type commands and decompression is
 * applied automatically to values in GET-type commands.
 */
public enum CompressionBackend {
    /**
     * Use Zstandard (zstd) compression backend.
     *
     * <p>ZSTD provides excellent compression ratios with good performance. Default compression level
     * is 3. Valid compression levels: -131072 to 22 (negative values enable fast mode).
     */
    ZSTD,

    /**
     * Use LZ4 compression backend.
     *
     * <p>LZ4 provides very fast compression/decompression with moderate compression ratios. Default
     * compression level is 0. Valid compression levels: -128 to 12 (higher values provide better
     * compression).
     */
    LZ4
}
