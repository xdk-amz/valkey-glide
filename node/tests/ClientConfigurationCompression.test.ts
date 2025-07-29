/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */

import {
    BaseClientConfiguration,
    CompressionBackend,
    CompressionConfiguration,
    GlideClientConfiguration,
    GlideClusterClientConfiguration,
} from "../src";

describe("Client Configuration with Compression", () => {
    const baseConfig: BaseClientConfiguration = {
        addresses: [{ host: "localhost", port: 6379 }],
    };

    describe("BaseClientConfiguration with compression", () => {
        it("should accept valid compression configuration", () => {
            const compressionConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 64,
                maxCompressionSize: 1024,
            };

            const config: BaseClientConfiguration = {
                ...baseConfig,
                compression: compressionConfig,
            };

            expect(config.compression).toEqual(compressionConfig);
        });

        it("should accept compression configuration with minimal settings", () => {
            const compressionConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 64,
            };

            const config: BaseClientConfiguration = {
                ...baseConfig,
                compression: compressionConfig,
            };

            expect(config.compression).toEqual(compressionConfig);
        });

        it("should accept configuration without compression", () => {
            const config: BaseClientConfiguration = baseConfig;

            expect(config.compression).toBeUndefined();
        });

        it("should accept disabled compression configuration", () => {
            const compressionConfig: CompressionConfiguration = {
                enabled: false,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 64,
            };

            const config: BaseClientConfiguration = {
                ...baseConfig,
                compression: compressionConfig,
            };

            expect(config.compression).toEqual(compressionConfig);
        });
    });

    describe("GlideClientConfiguration with compression", () => {
        it("should accept compression configuration", () => {
            const compressionConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.LZ4,
                compressionLevel: 6,
                minCompressionSize: 128,
            };

            const config: GlideClientConfiguration = {
                ...baseConfig,
                databaseId: 1,
                compression: compressionConfig,
            };

            expect(config.compression).toEqual(compressionConfig);
            expect(config.databaseId).toBe(1);
        });

        it("should work with all GlideClientConfiguration features", () => {
            const compressionConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 64,
            };

            const config: GlideClientConfiguration = {
                ...baseConfig,
                databaseId: 2,
                compression: compressionConfig,
                clientName: "test-client",
                requestTimeout: 5000,
            };

            expect(config.compression).toEqual(compressionConfig);
            expect(config.databaseId).toBe(2);
            expect(config.clientName).toBe("test-client");
            expect(config.requestTimeout).toBe(5000);
        });
    });

    describe("GlideClusterClientConfiguration with compression", () => {
        it("should accept compression configuration", () => {
            const compressionConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 10,
                minCompressionSize: 32,
                maxCompressionSize: 2048,
            };

            const config: GlideClusterClientConfiguration = {
                ...baseConfig,
                compression: compressionConfig,
            };

            expect(config.compression).toEqual(compressionConfig);
        });

        it("should work with all GlideClusterClientConfiguration features", () => {
            const compressionConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.LZ4,
                minCompressionSize: 64,
            };

            const config: GlideClusterClientConfiguration = {
                ...baseConfig,
                compression: compressionConfig,
                periodicChecks: "enabledDefaultConfigs",
                clientName: "cluster-client",
            };

            expect(config.compression).toEqual(compressionConfig);
            expect(config.periodicChecks).toBe("enabledDefaultConfigs");
            expect(config.clientName).toBe("cluster-client");
        });
    });

    describe("Compression configuration validation in client config", () => {
        it("should validate compression configuration types", () => {
            // Test that TypeScript types are correctly enforced
            const validConfig: BaseClientConfiguration = {
                ...baseConfig,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    minCompressionSize: 64,
                },
            };

            expect(validConfig.compression?.enabled).toBe(true);
            expect(validConfig.compression?.backend).toBe(CompressionBackend.ZSTD);
            expect(validConfig.compression?.minCompressionSize).toBe(64);
        });

        it("should allow optional compression fields", () => {
            const config: BaseClientConfiguration = {
                ...baseConfig,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    minCompressionSize: 64,
                    // compressionLevel and maxCompressionSize are optional
                },
            };

            expect(config.compression?.compressionLevel).toBeUndefined();
            expect(config.compression?.maxCompressionSize).toBeUndefined();
        });
    });
});
