/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */


/**
 * Enum representing the compression backend to use for automatic compression.
 */
export enum CompressionBackend {
    /**
     * Use zstd compression backend.
     */
    ZSTD = "ZSTD",
    /**
     * Use lz4 compression backend.
     */
    LZ4 = "LZ4",
}

/**
 * Configuration for automatic compression of values.
 * 
 * @remarks
 * This configuration enables transparent compression and decompression of values
 * for set-type and get-type commands respectively. When enabled, values will be
 * automatically compressed before being sent to the server and decompressed when
 * received from the server.
 * 
 * The compression is completely transparent to the application layer and maintains
 * full backward compatibility with existing data and non-compression clients.
 * 
 * @example
 * ```typescript
 * const compressionConfig: CompressionConfiguration = {
 *   enabled: true,
 *   backend: CompressionBackend.ZSTD,
 *   compressionLevel: 3,
 *   minCompressionSize: 64,
 *   maxCompressionSize: 1024 * 1024, // 1MB
 * };
 * ```
 */
export interface CompressionConfiguration {
    /**
     * Whether compression is enabled.
     * @default false
     */
    enabled: boolean;

    /**
     * The compression backend to use.
     * @default CompressionBackend.ZSTD
     */
    backend: CompressionBackend;

    /**
     * The compression level to use. If not set, the backend's default level will be used.
     * 
     * Valid ranges:
     * - ZSTD: 1-22 (higher values provide better compression but slower speed)
     * - LZ4: 1-12 (higher values provide better compression but slower speed)
     * 
     * @default undefined (uses backend default)
     */
    compressionLevel?: number;

    /**
     * The minimum size in bytes for values to be compressed.
     * Values smaller than this will not be compressed to avoid overhead.
     * @default 64
     */
    minCompressionSize: number;

    /**
     * The maximum size in bytes for values to be compressed.
     * Values larger than this will not be compressed.
     * If not set, no maximum limit is applied.
     * @default undefined (no limit)
     */
    maxCompressionSize?: number;
}

/**
 * Validates compression configuration parameters.
 * 
 * @param config - The compression configuration to validate
 * @throws {ConfigurationError} If any configuration parameter is invalid
 * 
 * @example
 * ```typescript
 * const config: CompressionConfiguration = {
 *   enabled: true,
 *   backend: CompressionBackend.ZSTD,
 *   compressionLevel: 3,
 *   minCompressionSize: 64,
 *   maxCompressionSize: 1024,
 * };
 * 
 * validateCompressionConfiguration(config); // Throws if invalid
 * ```
 */
export function validateCompressionConfiguration(
    config: CompressionConfiguration,
): void {
    if (config.minCompressionSize < 0) {
        throw new ConfigurationError(
            "minCompressionSize must be non-negative",
        );
    }

    if (config.maxCompressionSize !== undefined) {
        if (config.maxCompressionSize < 0) {
            throw new ConfigurationError(
                "maxCompressionSize must be non-negative",
            );
        }
        if (config.maxCompressionSize < config.minCompressionSize) {
            throw new ConfigurationError(
                "maxCompressionSize must be greater than or equal to minCompressionSize",
            );
        }
    }

    if (config.compressionLevel !== undefined) {
        // Validate compression level based on backend
        if (config.backend === CompressionBackend.ZSTD) {
            if (config.compressionLevel < 1 || config.compressionLevel > 22) {
                throw new ConfigurationError(
                    "compressionLevel for ZSTD backend must be between 1 and 22",
                );
            }
        } else if (config.backend === CompressionBackend.LZ4) {
            if (config.compressionLevel < 1 || config.compressionLevel > 12) {
                throw new ConfigurationError(
                    "compressionLevel for LZ4 backend must be between 1 and 12",
                );
            }
        }
    }
}

/**
 * Creates a compression configuration with default values.
 * 
 * @param overrides - Optional overrides for default values
 * @returns A validated compression configuration
 * 
 * @example
 * ```typescript
 * // Create with defaults
 * const defaultConfig = createCompressionConfiguration();
 * 
 * // Create with overrides
 * const customConfig = createCompressionConfiguration({
 *   enabled: true,
 *   backend: CompressionBackend.LZ4,
 *   compressionLevel: 6,
 * });
 * ```
 */
export function createCompressionConfiguration(
    overrides: Partial<CompressionConfiguration> = {},
): CompressionConfiguration {
    const config: CompressionConfiguration = {
        enabled: false,
        backend: CompressionBackend.ZSTD,
        minCompressionSize: 64,
        ...overrides,
    };

    validateCompressionConfiguration(config);
    return config;
}
