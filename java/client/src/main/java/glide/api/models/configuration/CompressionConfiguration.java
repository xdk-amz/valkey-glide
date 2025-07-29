/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

import glide.api.models.exceptions.ConfigurationError;
import lombok.Builder;
import lombok.Getter;
import lombok.NonNull;

/**
 * Configuration for automatic compression of values.
 *
 * <p>This configuration enables transparent compression and decompression of values for set-type
 * and get-type commands respectively. When enabled, values will be automatically compressed before
 * being sent to the server and decompressed when received from the server.
 *
 * <p>The compression is completely transparent to the application layer and maintains full backward
 * compatibility with existing data and non-compression clients.
 *
 * @example
 *     <pre>{@code
 * CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
 *     .enabled(true)
 *     .backend(CompressionBackend.ZSTD)
 *     .compressionLevel(3)
 *     .minCompressionSize(64)
 *     .maxCompressionSize(1024 * 1024) // 1MB
 *     .build();
 * }</pre>
 */
@Getter
@Builder
public class CompressionConfiguration {

    /**
     * Whether compression is enabled.
     *
     * @apiNote Defaults to {@code false}.
     */
    @Builder.Default private final boolean enabled = false;

    /**
     * The compression backend to use.
     *
     * @apiNote Defaults to {@link CompressionBackend#ZSTD}.
     */
    @NonNull @Builder.Default private final CompressionBackend backend = CompressionBackend.ZSTD;

    /**
     * The compression level to use. If not set, the backend's default level will be used.
     *
     * <p>Valid ranges:
     *
     * <ul>
     *   <li>ZSTD: 1-22 (higher values provide better compression but slower speed)
     *   <li>LZ4: 1-12 (higher values provide better compression but slower speed)
     * </ul>
     *
     * @apiNote Defaults to {@code null} (uses backend default).
     */
    private final Integer compressionLevel;

    /**
     * The minimum size in bytes for values to be compressed. Values smaller than this will not be
     * compressed to avoid overhead.
     *
     * @apiNote Defaults to {@code 64} bytes.
     */
    @Builder.Default private final int minCompressionSize = 64;

    /**
     * The maximum size in bytes for values to be compressed. Values larger than this will not be
     * compressed. If not set, no maximum limit is applied.
     *
     * @apiNote Defaults to {@code null} (no limit).
     */
    private final Integer maxCompressionSize;

    /**
     * Validates the compression configuration parameters.
     *
     * @throws ConfigurationError if any configuration parameter is invalid
     */
    public void validate() throws ConfigurationError {
        if (minCompressionSize < 0) {
            throw new ConfigurationError("minCompressionSize must be non-negative");
        }

        if (maxCompressionSize != null) {
            if (maxCompressionSize < 0) {
                throw new ConfigurationError("maxCompressionSize must be non-negative");
            }
            if (maxCompressionSize < minCompressionSize) {
                throw new ConfigurationError(
                        "maxCompressionSize must be greater than or equal to minCompressionSize");
            }
        }

        if (compressionLevel != null) {
            // Validate compression level based on backend
            switch (backend) {
                case ZSTD:
                    if (compressionLevel < 1 || compressionLevel > 22) {
                        throw new ConfigurationError(
                                "compressionLevel for ZSTD backend must be between 1 and 22");
                    }
                    break;
                case LZ4:
                    if (compressionLevel < 1 || compressionLevel > 12) {
                        throw new ConfigurationError(
                                "compressionLevel for LZ4 backend must be between 1 and 12");
                    }
                    break;
                default:
                    throw new ConfigurationError("Unsupported compression backend: " + backend);
            }
        }
    }
}
