/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */

import {
    afterAll,
    afterEach,
    beforeAll,
    describe,
    expect,
    it,
} from "@jest/globals";
import { ValkeyCluster } from "../../utils/TestUtils.js";
import {
    BaseClientConfiguration,
    Batch,
    ClusterBatch,
    CompressionBackend,
    CompressionConfiguration,
    ConfigurationError,
    GlideClient,
    GlideClusterClient,
    ProtocolVersion,
} from "../build-ts";
import {
    flushAndCloseClient,
    getClientConfigurationOption,
    getRandomKey,
    getServerVersion,
    parseEndpoints,
} from "./TestUtilities";

const TIMEOUT = 50000;
const CLEANUP_TIMEOUT = 10000;

// --- Data Generation Helpers ---

function generateCompressibleText(sizeBytes: number): string {
    const pattern = "A".repeat(10) + "B".repeat(10) + "C".repeat(10);
    let result = "";

    while (result.length < sizeBytes) {
        result += pattern;
    }

    return result.substring(0, sizeBytes);
}

function generateJsonData(sizeBytes: number): string {
    const baseObj = {
        id: 12345,
        name: "Test User",
        email: "test@example.com",
        description: "A".repeat(100),
        metadata: { key: "value" },
        tags: ["tag1", "tag2", "tag3"],
    };
    const jsonStr = JSON.stringify(baseObj);
    let result = "";

    while (result.length < sizeBytes) {
        result += jsonStr;
    }

    return result.substring(0, sizeBytes);
}

function generateBase64Data(sizeBytes: number): string {
    const chars =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let result = "";

    for (let i = 0; i < sizeBytes; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }

    return result;
}

// --- Known stat keys returned by getStatistics() for compression ---
const KNOWN_COMPRESSION_STAT_KEYS = new Set([
    "total_values_compressed",
    "total_bytes_compressed",
    "total_original_bytes",
    "compression_skipped_count",
]);

// --- Helper to get numeric stat with key validation ---
function getStatNum(
    stats: Record<string, string>,
    key: string,
): number {
    if (KNOWN_COMPRESSION_STAT_KEYS.has(key) && !(key in stats)) {
        throw new Error(
            `Expected stat key "${key}" not found in statistics object. ` +
            `Available keys: ${Object.keys(stats).join(", ")}`,
        );
    }

    return parseInt(stats[key] ?? "0", 10);
}

// --- Helper to assert the byte-size invariant: compressed < original ---
function expectCompressionShrunk(
    statsBefore: Record<string, string>,
    statsAfter: Record<string, string>,
): void {
    const originalDelta =
        getStatNum(statsAfter, "total_original_bytes") -
        getStatNum(statsBefore, "total_original_bytes");
    const compressedDelta =
        getStatNum(statsAfter, "total_bytes_compressed") -
        getStatNum(statsBefore, "total_bytes_compressed");
    expect(compressedDelta).toBeGreaterThan(0);
    expect(compressedDelta).toBeLessThan(originalDelta);
}

// --- Helper to create a compression-enabled client ---
async function createCompressionClient(
    addresses: [string, number][],
    clusterMode: boolean,
    protocol: ProtocolVersion,
    compression: CompressionConfiguration,
): Promise<GlideClient | GlideClusterClient> {
    const config: BaseClientConfiguration = getClientConfigurationOption(
        addresses,
        protocol,
        { compression },
    );

    if (clusterMode) {
        return await GlideClusterClient.createClient(config);
    }

    return await GlideClient.createClient(config);
}

// ============================================================
// Standalone Tests
// ============================================================
describe("Compression - Standalone", () => {
    let testsFailed = 0;
    let cluster: ValkeyCluster;
    let client: GlideClient | GlideClusterClient | undefined;

    beforeAll(async () => {
        const standaloneAddresses = global.STAND_ALONE_ENDPOINT as string;
        cluster = standaloneAddresses
            ? await ValkeyCluster.initFromExistingCluster(
                  false,
                  parseEndpoints(standaloneAddresses),
                  getServerVersion,
              )
            : await ValkeyCluster.createCluster(
                  false,
                  1,
                  1,
                  getServerVersion,
              );
    }, 20000);

    afterEach(async () => {
        await flushAndCloseClient(
            false,
            cluster?.getAddresses(),
            client,
        );
        client = undefined;
    });

    afterAll(async () => {
        if (testsFailed === 0) {
            await cluster?.close();
        } else {
            await cluster?.close(true);
        }
    }, CLEANUP_TIMEOUT);

    // --- Basic Compression Tests ---

    it(
        "basic SET/GET with ZSTD compression",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );
            const key = `compression_basic_${getRandomKey()}`;
            const value = generateCompressibleText(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    it(
        "basic SET/GET with LZ4 compression",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.LZ4 },
            );
            const key = `compression_lz4_${getRandomKey()}`;
            const value = generateCompressibleText(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    it(
        "compression respects min_compression_size threshold",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    minCompressionSize: 64,
                },
            );

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialSkipped = getStatNum(initialStats, "compression_skipped_count");
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            // Below threshold - should be skipped
            for (const size of [32, 48, 63]) {
                const key = `below_threshold_${size}_${getRandomKey()}`;
                const value = generateCompressibleText(size);
                await client.set(key, value);
                expect((await client.get(key))?.toString()).toBe(value);
            }

            let stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "compression_skipped_count")).toBeGreaterThan(
                initialSkipped,
            );
            expect(getStatNum(stats, "total_values_compressed")).toBe(
                initialCompressed,
            );

            // Above threshold - should be compressed
            const midCompressed = getStatNum(stats, "total_values_compressed");
            const midStats = { ...stats };

            for (const size of [64, 128, 256]) {
                const key = `above_threshold_${size}_${getRandomKey()}`;
                const value = generateCompressibleText(size);
                await client.set(key, value);
                expect((await client.get(key))?.toString()).toBe(value);
            }

            stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                midCompressed,
            );
            expectCompressionShrunk(midStats, stats);
        },
        TIMEOUT,
    );

    it(
        "compression disabled by default - no compression applied",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: false },
            );

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");
            const initialSkipped = getStatNum(initialStats, "compression_skipped_count");

            for (const size of [64, 1024, 10240]) {
                const key = `no_compression_${size}_${getRandomKey()}`;
                const value = generateCompressibleText(size);
                expect(await client.set(key, value)).toBe("OK");
                expect((await client.get(key))?.toString()).toBe(value);
            }

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBe(
                initialCompressed,
            );
            expect(getStatNum(stats, "compression_skipped_count")).toBe(
                initialSkipped,
            );
        },
        TIMEOUT,
    );

    // --- Data Type Tests ---

    it.each([
        ["compressible_text", generateCompressibleText],
        ["json", generateJsonData],
        ["base64", generateBase64Data],
    ])(
        "compression with %s data type",
        async (dataType, generator) => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `dtype_${dataType}_${getRandomKey()}`;
            const value = generator(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    // --- Various sizes ---

    it.each([512, 1024, 10240, 102400])(
        "compression with %d byte values",
        async (dataSize) => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `size_${dataSize}_${getRandomKey()}`;
            const value = generateCompressibleText(dataSize);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");
            const initialOriginal = getStatNum(initialStats, "total_original_bytes");
            const initialBytesCompressed = getStatNum(initialStats, "total_bytes_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );

            // Invariant: compressed bytes <= original bytes
            const addedOriginal =
                getStatNum(stats, "total_original_bytes") - initialOriginal;
            const addedCompressed =
                getStatNum(stats, "total_bytes_compressed") - initialBytesCompressed;
            expect(addedCompressed).toBeLessThanOrEqual(addedOriginal);
        },
        TIMEOUT,
    );

    // --- Edge Cases ---

    it(
        "compression with empty value",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `empty_${getRandomKey()}`;
            const initialStats = client.getStatistics() as Record<string, string>;
            const initialSkipped = getStatNum(initialStats, "compression_skipped_count");
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, "")).toBe("OK");
            expect((await client.get(key))?.toString()).toBe("");

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "compression_skipped_count")).toBeGreaterThan(
                initialSkipped,
            );
            expect(getStatNum(stats, "total_values_compressed")).toBe(
                initialCompressed,
            );
        },
        TIMEOUT,
    );

    it(
        "compression with very large value (10MB)",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `very_large_${getRandomKey()}`;
            const size = 10 * 1024 * 1024; // 10MB
            const value = generateCompressibleText(size);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    it(
        "data written with one backend readable by another",
        async () => {
            // Write with ZSTD
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `backend_mismatch_${getRandomKey()}`;
            const value = generateCompressibleText(10240);
            await client.set(key, value);
            client.close();

            // Read with LZ4 - data should still be readable
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.LZ4 },
            );

            expect((await client.get(key))?.toString()).toBe(value);
        },
        TIMEOUT,
    );

    // --- Batch Tests ---

    it(
        "compression in batch operations",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const numKeys = 50;
            const keyPrefix = `batch_${getRandomKey()}`;
            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            const batch = new Batch(false);
            const keysAndValues: [string, string][] = [];

            for (let i = 0; i < numKeys; i++) {
                const key = `${keyPrefix}_${i}`;
                const value = generateCompressibleText(
                    1024 + Math.floor(Math.random() * 9216),
                );
                keysAndValues.push([key, value]);
                batch.set(key, value);
            }

            const results = await (client as GlideClient).exec(batch, true);
            expect(results).not.toBeNull();
            expect(results!.every((r) => r === "OK")).toBe(true);

            const stats = client.getStatistics() as Record<string, string>;
            const compressedCount =
                getStatNum(stats, "total_values_compressed") - initialCompressed;
            expect(compressedCount).toBe(numKeys);
            expectCompressionShrunk(initialStats, stats);

            // Verify values
            for (const [key, expectedValue] of keysAndValues) {
                expect((await client.get(key))?.toString()).toBe(expectedValue);
            }
        },
        TIMEOUT,
    );

    it(
        "batch with mixed sizes - some below threshold",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    minCompressionSize: 64,
                },
            );

            const keyPrefix = `mixed_batch_${getRandomKey()}`;
            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");
            const initialSkipped = getStatNum(initialStats, "compression_skipped_count");

            const batch = new Batch(false);
            const keysAndValues: [string, string][] = [];

            // 10 small values (below threshold)
            for (let i = 0; i < 10; i++) {
                const key = `${keyPrefix}_small_${i}`;
                const value = generateCompressibleText(32);
                keysAndValues.push([key, value]);
                batch.set(key, value);
            }

            // 10 large values (above threshold)
            for (let i = 0; i < 10; i++) {
                const key = `${keyPrefix}_large_${i}`;
                const value = generateCompressibleText(5120);
                keysAndValues.push([key, value]);
                batch.set(key, value);
            }

            const results = await (client as GlideClient).exec(batch, true);
            expect(results).not.toBeNull();
            expect(results!.every((r) => r === "OK")).toBe(true);

            const stats = client.getStatistics() as Record<string, string>;
            const skippedCount =
                getStatNum(stats, "compression_skipped_count") - initialSkipped;
            const compressedCount =
                getStatNum(stats, "total_values_compressed") - initialCompressed;

            expect(skippedCount).toBe(10);
            expect(compressedCount).toBe(10);
            expectCompressionShrunk(initialStats, stats);

            // Verify all values
            for (const [key, expectedValue] of keysAndValues) {
                expect((await client.get(key))?.toString()).toBe(expectedValue);
            }
        },
        TIMEOUT,
    );

    // --- Compression with TTL ---

    it(
        "compression with TTL",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `ttl_${getRandomKey()}`;
            const value = generateCompressibleText(10240);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect(await client.expire(key, 10)).toBe(true);
            expect((await client.get(key))?.toString()).toBe(value);

            const ttl = await client.ttl(key);
            expect(ttl).toBeGreaterThan(0);
            expect(ttl).toBeLessThanOrEqual(10);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    // --- Backend Level Validation ---

    it.each([
        [CompressionBackend.ZSTD, 1],
        [CompressionBackend.ZSTD, 3],
        [CompressionBackend.ZSTD, 10],
        [CompressionBackend.ZSTD, 22],
        [CompressionBackend.LZ4, 0],
        [CompressionBackend.LZ4, 1],
        [CompressionBackend.LZ4, 6],
        [CompressionBackend.LZ4, 12],
    ])(
        "valid compression level: backend=%d level=%d",
        async (backend, level) => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                {
                    enabled: true,
                    backend,
                    compressionLevel: level,
                    minCompressionSize: 64,
                },
            );

            const key = `level_${backend}_${level}_${getRandomKey()}`;
            const value = generateCompressibleText(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    it.each([
        [CompressionBackend.ZSTD, 23],
        [CompressionBackend.ZSTD, 100],
        [CompressionBackend.ZSTD, -200000],
        [CompressionBackend.LZ4, 13],
        [CompressionBackend.LZ4, 100],
        [CompressionBackend.LZ4, -129],
        [CompressionBackend.LZ4, -1000],
    ])(
        "invalid compression level rejected: backend=%d level=%d",
        async (backend, invalidLevel) => {
            await expect(
                createCompressionClient(
                    cluster.getAddresses(),
                    false,
                    ProtocolVersion.RESP3,
                    {
                        enabled: true,
                        backend,
                        compressionLevel: invalidLevel,
                        minCompressionSize: 64,
                    },
                ),
            ).rejects.toThrow();
        },
        TIMEOUT,
    );

    // --- Configuration Validation ---

    it("rejects minCompressionSize below minimum", () => {
        expect(() => {
            getClientConfigurationOption(
                cluster.getAddresses(),
                ProtocolVersion.RESP3,
                {
                    compression: {
                        enabled: true,
                        backend: CompressionBackend.ZSTD,
                        minCompressionSize: 1, // Below MIN_COMPRESSED_SIZE (6)
                    },
                },
            );
            // The validation happens during createClientRequest, so we need to actually create a client
        }).not.toThrow(); // getClientConfigurationOption doesn't validate

        // The actual validation happens during client creation
        expect(
            createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP3,
                {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    minCompressionSize: 1,
                },
            ),
        ).rejects.toThrow(ConfigurationError);
    });

    // --- RESP2 Protocol ---

    it(
        "compression works with RESP2 protocol",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                false,
                ProtocolVersion.RESP2,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `resp2_${getRandomKey()}`;
            const value = generateCompressibleText(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );
});

// ============================================================
// Cluster Mode Tests
// ============================================================
describe("Compression - Cluster", () => {
    let testsFailed = 0;
    let cluster: ValkeyCluster;
    let client: GlideClient | GlideClusterClient | undefined;

    beforeAll(async () => {
        const clusterAddresses = global.CLUSTER_ENDPOINTS as string;
        cluster = clusterAddresses
            ? await ValkeyCluster.initFromExistingCluster(
                  true,
                  parseEndpoints(clusterAddresses),
                  getServerVersion,
              )
            : await ValkeyCluster.createCluster(
                  true,
                  3,
                  1,
                  getServerVersion,
              );
    }, 20000);

    afterEach(async () => {
        await flushAndCloseClient(
            true,
            cluster?.getAddresses(),
            client,
        );
        client = undefined;
    });

    afterAll(async () => {
        if (testsFailed === 0) {
            await cluster?.close();
        } else {
            await cluster?.close(true);
        }
    }, CLEANUP_TIMEOUT);

    it(
        "basic SET/GET with ZSTD compression in cluster mode",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                true,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `cluster_zstd_${getRandomKey()}`;
            const value = generateCompressibleText(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    it(
        "basic SET/GET with LZ4 compression in cluster mode",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                true,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.LZ4 },
            );

            const key = `cluster_lz4_${getRandomKey()}`;
            const value = generateCompressibleText(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );

    it(
        "compression across multiple slots in cluster mode",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                true,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const numKeys = 50;
            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            const keysAndValues: [string, string][] = [];

            for (let i = 0; i < numKeys; i++) {
                const key = `multislot_${i}_${getRandomKey()}`;
                const value = generateCompressibleText(5120);
                keysAndValues.push([key, value]);
                expect(await client.set(key, value)).toBe("OK");
            }

            const stats = client.getStatistics() as Record<string, string>;
            const compressedCount =
                getStatNum(stats, "total_values_compressed") - initialCompressed;
            expect(compressedCount).toBe(numKeys);
            expectCompressionShrunk(initialStats, stats);

            // Verify all values
            for (const [key, expectedValue] of keysAndValues) {
                expect((await client.get(key))?.toString()).toBe(expectedValue);
            }
        },
        TIMEOUT,
    );

    it(
        "cluster batch with compression",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                true,
                ProtocolVersion.RESP3,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const numKeys = 50;
            const keyPrefix = `cluster_batch_${getRandomKey()}`;
            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            const batch = new ClusterBatch(false);
            const keysAndValues: [string, string][] = [];

            for (let i = 0; i < numKeys; i++) {
                const key = `${keyPrefix}_${i}`;
                const value = generateCompressibleText(1024);
                keysAndValues.push([key, value]);
                batch.set(key, value);
            }

            const results = await (client as GlideClusterClient).exec(
                batch,
                true,
            );
            expect(results).not.toBeNull();
            expect(results!.every((r) => r === "OK")).toBe(true);

            const stats = client.getStatistics() as Record<string, string>;
            const compressedCount =
                getStatNum(stats, "total_values_compressed") - initialCompressed;
            expect(compressedCount).toBe(numKeys);
            expectCompressionShrunk(initialStats, stats);

            // Verify values
            for (const [key, expectedValue] of keysAndValues) {
                expect((await client.get(key))?.toString()).toBe(expectedValue);
            }
        },
        TIMEOUT,
    );

    it(
        "compression with RESP2 in cluster mode",
        async () => {
            client = await createCompressionClient(
                cluster.getAddresses(),
                true,
                ProtocolVersion.RESP2,
                { enabled: true, backend: CompressionBackend.ZSTD },
            );

            const key = `cluster_resp2_${getRandomKey()}`;
            const value = generateCompressibleText(1024);

            const initialStats = client.getStatistics() as Record<string, string>;
            const initialCompressed = getStatNum(initialStats, "total_values_compressed");

            expect(await client.set(key, value)).toBe("OK");
            expect((await client.get(key))?.toString()).toBe(value);

            const stats = client.getStatistics() as Record<string, string>;
            expect(getStatNum(stats, "total_values_compressed")).toBeGreaterThan(
                initialCompressed,
            );
            expectCompressionShrunk(initialStats, stats);
        },
        TIMEOUT,
    );
});
