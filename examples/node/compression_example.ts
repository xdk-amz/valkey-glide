/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */

import {
    ClosingError,
    CompressionBackend,
    CompressionConfiguration,
    ConnectionError,
    GlideClient,
    Logger,
    RequestError,
    TimeoutError,
} from "@valkey/valkey-glide";

/** Known stat keys that must be present when compression is configured. */
const REQUIRED_COMPRESSION_STAT_KEYS = [
    "total_values_compressed",
    "total_bytes_compressed",
    "total_original_bytes",
    "compression_skipped_count",
];

/** Helper to read a numeric stat, throwing if a known key is missing. */
function statNum(stats: Record<string, string>, key: string): number {
    if (REQUIRED_COMPRESSION_STAT_KEYS.includes(key) && !(key in stats)) {
        throw new Error(
            `Expected stat key "${key}" not found. ` +
                `Available keys: ${Object.keys(stats).join(", ")}`,
        );
    }

    return parseInt(stats[key] ?? "0", 10);
}

/** Runtime assertion helper - throws on failure. */
function assert(condition: boolean, message: string): void {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

/**
 * Creates and returns a GlideClient with compression enabled.
 *
 * This example demonstrates how to configure transparent compression
 * using the ZSTD backend. Values sent to the server will be automatically
 * compressed and decompressed transparently on read.
 *
 * @param nodesList - List of server nodes to connect to.
 * @returns A compression-enabled GlideClient instance.
 */
async function createClientWithCompression(
    nodesList = [{ host: "localhost", port: 6379 }],
) {
    const compression: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        compressionLevel: 3,
        minCompressionSize: 64,
    };

    return await GlideClient.createClient({
        addresses: nodesList,
        requestTimeout: 500,
        compression,
    });
}

/**
 * Demonstrates basic compression usage with SET/GET operations,
 * using statistics to verify compression behavior.
 */
async function appLogic(client: GlideClient) {
    // --- Small value (below minCompressionSize threshold) ---
    const statsBefore = client.getStatistics() as Record<string, string>;
    const skippedBefore = statNum(statsBefore, "compression_skipped_count");
    const compressedBefore = statNum(statsBefore, "total_values_compressed");

    const smallValue = "hello";
    await client.set("small_key", smallValue);
    const smallResult = await client.get("small_key");

    const statsAfterSmall = client.getStatistics() as Record<string, string>;
    const skippedAfterSmall = statNum(statsAfterSmall, "compression_skipped_count");
    const compressedAfterSmall = statNum(statsAfterSmall, "total_values_compressed");

    Logger.log(
        "info",
        "app",
        `Small value retrieved: "${smallResult?.toString()}" | ` +
            `skipped: ${skippedAfterSmall - skippedBefore} (expected 1), ` +
            `compressed: ${compressedAfterSmall - compressedBefore} (expected 0)`,
    );

    // Assert: small value was skipped, not compressed
    assert(
        smallResult?.toString() === smallValue,
        "Small value data integrity check failed",
    );
    assert(
        skippedAfterSmall - skippedBefore === 1,
        `Expected 1 skip for small value, got ${skippedAfterSmall - skippedBefore}`,
    );
    assert(
        compressedAfterSmall === compressedBefore,
        `Expected no compression for small value, but count changed by ${compressedAfterSmall - compressedBefore}`,
    );

    // --- Large value (above threshold) ---
    const statsBeforeLarge = client.getStatistics() as Record<string, string>;
    const compressedBeforeLarge = statNum(statsBeforeLarge, "total_values_compressed");
    const originalBytesBefore = statNum(statsBeforeLarge, "total_original_bytes");
    const compressedBytesBefore = statNum(statsBeforeLarge, "total_bytes_compressed");

    const largeValue = "A".repeat(1024); // 1KB of repeated data, highly compressible
    await client.set("large_key", largeValue);
    const largeResult = await client.get("large_key");

    const statsAfterLarge = client.getStatistics() as Record<string, string>;
    const compressedAfterLarge = statNum(statsAfterLarge, "total_values_compressed");
    const originalBytesAfter = statNum(statsAfterLarge, "total_original_bytes");
    const compressedBytesAfter = statNum(statsAfterLarge, "total_bytes_compressed");

    const originalDelta = originalBytesAfter - originalBytesBefore;
    const compressedDelta = compressedBytesAfter - compressedBytesBefore;

    Logger.log(
        "info",
        "app",
        `Large value - data integrity: ${largeResult?.toString() === largeValue} | ` +
            `compressed: ${compressedAfterLarge - compressedBeforeLarge} (expected 1), ` +
            `original bytes: ${originalDelta}, compressed bytes: ${compressedDelta}, ` +
            `ratio: ${((1 - compressedDelta / originalDelta) * 100).toFixed(1)}% savings`,
    );

    // Assert: large value was compressed with correct byte-size invariant
    assert(
        largeResult?.toString() === largeValue,
        "Large value data integrity check failed",
    );
    assert(
        compressedAfterLarge - compressedBeforeLarge === 1,
        `Expected 1 compression for large value, got ${compressedAfterLarge - compressedBeforeLarge}`,
    );
    assert(
        compressedDelta > 0 && compressedDelta < originalDelta,
        `Byte-size invariant violated: compressed (${compressedDelta}) must be > 0 and < original (${originalDelta})`,
    );
}

/**
 * Demonstrates creating a client with LZ4 compression backend,
 * using statistics to verify compression occurred.
 */
async function lz4Example() {
    const compression: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.LZ4,
        compressionLevel: 0,
        minCompressionSize: 64,
    };

    let client: GlideClient | undefined;

    try {
        client = await GlideClient.createClient({
            addresses: [{ host: "localhost", port: 6379 }],
            requestTimeout: 500,
            compression,
        });

        const statsBefore = client.getStatistics() as Record<string, string>;
        const compressedBefore = statNum(statsBefore, "total_values_compressed");
        const originalBytesBefore = statNum(statsBefore, "total_original_bytes");
        const compressedBytesBefore = statNum(statsBefore, "total_bytes_compressed");

        const value = "B".repeat(2048);
        await client.set("lz4_key", value);
        const result = await client.get("lz4_key");

        const statsAfter = client.getStatistics() as Record<string, string>;
        const compressedAfter = statNum(statsAfter, "total_values_compressed");
        const originalDelta = statNum(statsAfter, "total_original_bytes") - originalBytesBefore;
        const compressedDelta = statNum(statsAfter, "total_bytes_compressed") - compressedBytesBefore;

        Logger.log(
            "info",
            "app",
            `LZ4 - data integrity: ${result?.toString() === value} | ` +
                `compressed: ${compressedAfter - compressedBefore} (expected 1), ` +
                `original bytes: ${originalDelta}, compressed bytes: ${compressedDelta}, ` +
                `ratio: ${((1 - compressedDelta / originalDelta) * 100).toFixed(1)}% savings`,
        );

        // Assert: LZ4 compression occurred with correct byte-size invariant
        assert(
            result?.toString() === value,
            "LZ4 data integrity check failed",
        );
        assert(
            compressedAfter - compressedBefore === 1,
            `Expected 1 LZ4 compression, got ${compressedAfter - compressedBefore}`,
        );
        assert(
            compressedDelta > 0 && compressedDelta < originalDelta,
            `LZ4 byte-size invariant violated: compressed (${compressedDelta}) must be > 0 and < original (${originalDelta})`,
        );
    } finally {
        client?.close();
    }
}

async function main() {
    let client: GlideClient | undefined;

    try {
        client = await createClientWithCompression();
        await appLogic(client);
        await lz4Example();
    } catch (error) {
        if (
            error instanceof ClosingError ||
            error instanceof ConnectionError ||
            error instanceof RequestError ||
            error instanceof TimeoutError
        ) {
            Logger.log(
                "error",
                "app",
                `Glide error: ${(error as Error).message}`,
            );
        } else {
            Logger.log("error", "app", `Unexpected error: ${error}`);
        }
    } finally {
        client?.close();
    }
}

main();
