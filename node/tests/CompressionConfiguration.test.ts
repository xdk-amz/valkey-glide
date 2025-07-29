/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */

import {
    CompressionBackend,
    CompressionConfiguration,
    createCompressionConfiguration,
    validateCompressionConfiguration,
} from "../src/CompressionConfiguration";
import { ConfigurationError } from "../src/Errors";

describe("CompressionConfiguration", () => {
    describe("CompressionBackend enum", () => {
        it("should have correct values", () => {
            expect(CompressionBackend.ZSTD).toBe("ZSTD");
            expect(CompressionBackend.LZ4).toBe("LZ4");
        });
    });

    describe("validateCompressionConfiguration", () => {
        it("should validate valid configuration", () => {
            const config: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 64,
                maxCompressionSize: 1024,
            };

            expect(() => validateCompressionConfiguration(config)).not.toThrow();
        });

        it("should validate configuration without optional fields", () => {
            const config: CompressionConfiguration = {
                enabled: false,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 64,
            };

            expect(() => validateCompressionConfiguration(config)).not.toThrow();
        });

        it("should throw error for negative minCompressionSize", () => {
            const config: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: -1,
            };

            expect(() => validateCompressionConfiguration(config)).toThrow(
                ConfigurationError,
            );
            expect(() => validateCompressionConfiguration(config)).toThrow(
                "minCompressionSize must be non-negative",
            );
        });

        it("should throw error for negative maxCompressionSize", () => {
            const config: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 64,
                maxCompressionSize: -1,
            };

            expect(() => validateCompressionConfiguration(config)).toThrow(
                ConfigurationError,
            );
            expect(() => validateCompressionConfiguration(config)).toThrow(
                "maxCompressionSize must be non-negative",
            );
        });

        it("should throw error when maxCompressionSize < minCompressionSize", () => {
            const config: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 100,
                maxCompressionSize: 50,
            };

            expect(() => validateCompressionConfiguration(config)).toThrow(
                ConfigurationError,
            );
            expect(() => validateCompressionConfiguration(config)).toThrow(
                "maxCompressionSize must be greater than or equal to minCompressionSize",
            );
        });

        it("should allow maxCompressionSize equal to minCompressionSize", () => {
            const config: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 64,
                maxCompressionSize: 64,
            };

            expect(() => validateCompressionConfiguration(config)).not.toThrow();
        });

        describe("ZSTD compression level validation", () => {
            it("should accept valid ZSTD compression levels", () => {
                const validLevels = [1, 3, 10, 22];

                validLevels.forEach((level) => {
                    const config: CompressionConfiguration = {
                        enabled: true,
                        backend: CompressionBackend.ZSTD,
                        compressionLevel: level,
                        minCompressionSize: 64,
                    };

                    expect(() => validateCompressionConfiguration(config)).not.toThrow();
                });
            });

            it("should reject invalid ZSTD compression levels", () => {
                const invalidLevels = [0, 23, -1, 100];

                invalidLevels.forEach((level) => {
                    const config: CompressionConfiguration = {
                        enabled: true,
                        backend: CompressionBackend.ZSTD,
                        compressionLevel: level,
                        minCompressionSize: 64,
                    };

                    expect(() => validateCompressionConfiguration(config)).toThrow(
                        ConfigurationError,
                    );
                    expect(() => validateCompressionConfiguration(config)).toThrow(
                        "compressionLevel for ZSTD backend must be between 1 and 22",
                    );
                });
            });
        });

        describe("LZ4 compression level validation", () => {
            it("should accept valid LZ4 compression levels", () => {
                const validLevels = [1, 6, 12];

                validLevels.forEach((level) => {
                    const config: CompressionConfiguration = {
                        enabled: true,
                        backend: CompressionBackend.LZ4,
                        compressionLevel: level,
                        minCompressionSize: 64,
                    };

                    expect(() => validateCompressionConfiguration(config)).not.toThrow();
                });
            });

            it("should reject invalid LZ4 compression levels", () => {
                const invalidLevels = [0, 13, -1, 100];

                invalidLevels.forEach((level) => {
                    const config: CompressionConfiguration = {
                        enabled: true,
                        backend: CompressionBackend.LZ4,
                        compressionLevel: level,
                        minCompressionSize: 64,
                    };

                    expect(() => validateCompressionConfiguration(config)).toThrow(
                        ConfigurationError,
                    );
                    expect(() => validateCompressionConfiguration(config)).toThrow(
                        "compressionLevel for LZ4 backend must be between 1 and 12",
                    );
                });
            });
        });
    });

    describe("createCompressionConfiguration", () => {
        it("should create configuration with default values", () => {
            const config = createCompressionConfiguration();

            expect(config.enabled).toBe(false);
            expect(config.backend).toBe(CompressionBackend.ZSTD);
            expect(config.minCompressionSize).toBe(64);
            expect(config.compressionLevel).toBeUndefined();
            expect(config.maxCompressionSize).toBeUndefined();
        });

        it("should create configuration with overrides", () => {
            const overrides: Partial<CompressionConfiguration> = {
                enabled: true,
                backend: CompressionBackend.LZ4,
                compressionLevel: 6,
                maxCompressionSize: 1024,
            };

            const config = createCompressionConfiguration(overrides);

            expect(config.enabled).toBe(true);
            expect(config.backend).toBe(CompressionBackend.LZ4);
            expect(config.compressionLevel).toBe(6);
            expect(config.minCompressionSize).toBe(64); // default
            expect(config.maxCompressionSize).toBe(1024);
        });

        it("should validate configuration during creation", () => {
            const invalidOverrides: Partial<CompressionConfiguration> = {
                enabled: true,
                minCompressionSize: -1,
            };

            expect(() => createCompressionConfiguration(invalidOverrides)).toThrow(
                ConfigurationError,
            );
        });

        it("should allow partial overrides", () => {
            const config = createCompressionConfiguration({
                enabled: true,
            });

            expect(config.enabled).toBe(true);
            expect(config.backend).toBe(CompressionBackend.ZSTD); // default
            expect(config.minCompressionSize).toBe(64); // default
        });
    });
});
