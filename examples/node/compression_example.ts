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
 * Demonstrates basic compression usage with SET/GET operations.
 */
async function appLogic(client: GlideClient) {
    // Small value (below minCompressionSize threshold) - will NOT be compressed
    const smallValue = "hello";
    await client.set("small_key", smallValue);
    const smallResult = await client.get("small_key");
    Logger.log(
        "info",
        "app",
        `Small value (not compressed): ${smallResult?.toString()}`,
    );

    // Large value (above threshold) - will be compressed transparently
    const largeValue = "A".repeat(1024); // 1KB of repeated data, highly compressible
    await client.set("large_key", largeValue);
    const largeResult = await client.get("large_key");
    Logger.log(
        "info",
        "app",
        `Large value length: ${largeResult?.toString().length} (original: ${largeValue.length})`,
    );

    // Verify data integrity
    Logger.log(
        "info",
        "app",
        `Data integrity check: ${largeResult?.toString() === largeValue}`,
    );

    // Check compression statistics
    const stats = client.getStatistics() as Record<string, string>;
    Logger.log(
        "info",
        "app",
        `Compression stats - values compressed: ${stats["total_values_compressed"]}, ` +
            `original bytes: ${stats["total_original_bytes"]}, ` +
            `compressed bytes: ${stats["total_bytes_compressed"]}`,
    );
}

/**
 * Demonstrates creating a client with LZ4 compression backend.
 */
async function lz4Example() {
    const compression: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.LZ4,
        compressionLevel: 0,
        minCompressionSize: 64,
    };

    const client = await GlideClient.createClient({
        addresses: [{ host: "localhost", port: 6379 }],
        requestTimeout: 500,
        compression,
    });

    const value = "B".repeat(2048);
    await client.set("lz4_key", value);
    const result = await client.get("lz4_key");
    Logger.log(
        "info",
        "app",
        `LZ4 compression - data integrity: ${result?.toString() === value}`,
    );

    client.close();
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
