/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

import lombok.Builder;
import lombok.Getter;
import lombok.NonNull;
import lombok.ToString;

/**
 * Configuration for automatic compression of values.
 *
 * <p>When enabled, the client will automatically compress values for SET-type commands and
 * decompress values for GET-type commands. This is transparent to the application.
 *
 * <p>Compression is only applied to values that meet the minimum size threshold. Smaller values are
 * not compressed to avoid overhead.
 *
 * @example
 *     <pre>{@code
 * // Enable compression with default settings (ZSTD, level 3, 64-byte threshold)
 * CompressionConfiguration config = CompressionConfiguration.builder()
 *     .enabled(true)
 *     .build();
 *
 * // Enable compression with custom settings
 * CompressionConfiguration config = CompressionConfiguration.builder()
 *     .enabled(true)
 *     .backend(CompressionBackend.LZ4)
 *     .compressionLevel(6)
 *     .minCompressionSize(128)
 *     .build();
 * }</pre>
 */
@Getter
@Builder
@ToString
public class CompressionConfiguration {
    /**
     * Whether compression is enabled.
     *
     * <p>When false, no compression or decompression is performed. Default: false
     */
    @Builder.Default private final boolean enabled = false;

    /**
     * The compression backend to use.
     *
     * <p>Default: {@link CompressionBackend#ZSTD}
     */
    @NonNull @Builder.Default private final CompressionBackend backend = CompressionBackend.ZSTD;

    /**
     * The compression level to use.
     *
     * <p>If not set, the backend's default level will be used:
     *
     * <ul>
     *   <li>ZSTD default: 3
     *   <li>LZ4 default: 0
     * </ul>
     *
     * <p>Valid ranges are backend-specific and validated by the Rust core:
     *
     * <ul>
     *   <li>ZSTD: -131072 to 22
     *   <li>LZ4: -128 to 12
     * </ul>
     *
     * <p>Higher levels generally provide better compression at the cost of speed. Negative levels may
     * enable fast modes depending on the backend.
     */
    private final Integer compressionLevel;

    /**
     * The minimum size in bytes for values to be compressed.
     *
     * <p>Values smaller than this threshold will not be compressed to avoid overhead. Must be at
     * least 6 bytes (5-byte header + 1 byte data).
     *
     * <p>Default: 64 bytes
     */
    @Builder.Default private final int minCompressionSize = 64;
}
