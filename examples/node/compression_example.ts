/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 * 
 * This example demonstrates how to use automatic compression with Valkey GLIDE.
 * It shows various compression configurations and use cases.
 */

import {
    CompressionBackend,
    CompressionConfiguration,
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    Logger
} from "@valkey/valkey-glide";

interface NodeAddress {
    host: string;
    port: number;
}

/**
 * Creates a GlideClient with compression configuration.
 */
async function createClientWithCompression(
    nodesList: NodeAddress[] = [{ host: "localhost", port: 6379 }],
    compressionConfig?: CompressionConfiguration,
    useCluster: boolean = false
): Promise<GlideClient | GlideClusterClient> {
    const addresses = nodesList.map(node => ({
        host: node.host,
        port: node.port,
    }));

    if (useCluster) {
        const config: GlideClusterClientConfiguration = {
            addresses: addresses,
            compression: compressionConfig,
            requestTimeout: 2000,
        };
        return await GlideClusterClient.createClient(config);
    } else {
        const config: GlideClientConfiguration = {
            addresses: addresses,
            compression: compressionConfig,
            requestTimeout: 2000,
        };
        return await GlideClient.createClient(config);
    }
}

/**
 * Demonstrates basic compression usage with default settings.
 */
async function basicCompressionExample(): Promise<void> {
    Logger.log("info", "compression_example", "=== Basic Compression Example ===");

    // Create compression configuration with defaults
    const compressionConfig: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        // compressionLevel defaults to 3
        // minCompressionSize defaults to 64 bytes
    };

    const client = await createClientWithCompression(undefined, compressionConfig) as GlideClient;

    try {
        // Store some data that will be compressed
        const largeJson = {
            user_id: "12345",
            name: "John Doe",
            email: "john.doe@example.com",
            preferences: {
                theme: "dark",
                language: "en",
                notifications: true
            },
            data: "x".repeat(1000)  // Large field to ensure compression
        };

        const jsonStr = JSON.stringify(largeJson);
        Logger.log("info", "compression_example", `Original JSON size: ${jsonStr.length} bytes`);

        // Set the data (will be automatically compressed)
        await client.set("user:12345", jsonStr);
        Logger.log("info", "compression_example", "Data stored with compression");

        // Get the data (will be automatically decompressed)
        const retrievedData = await client.get("user:12345");
        const retrievedJson = JSON.parse(retrievedData?.toString() || "{}");

        Logger.log("info", "compression_example", `Retrieved data matches: ${JSON.stringify(retrievedJson) === jsonStr}`);
        Logger.log("info", "compression_example", `Retrieved user: ${retrievedJson.name}`);

    } finally {
        client.close();
    }
}

/**
 * Demonstrates different compression configurations for various use cases.
 */
async function compressionConfigurationExamples(): Promise<void> {
    Logger.log("info", "compression_example", "=== Compression Configuration Examples ===");

    // High-performance configuration (fast compression)
    const highPerformanceConfig: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        compressionLevel: 1,  // Fastest compression
        minCompressionSize: 128,  // Skip smaller values
        maxCompressionSize: 1024 * 1024  // 1MB limit
    };

    // High-compression configuration (better compression ratio)
    const highCompressionConfig: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        compressionLevel: 6,  // Better compression
        minCompressionSize: 32,  // Compress more values
        maxCompressionSize: undefined  // No size limit
    };

    // Balanced configuration (recommended for most use cases)
    const balancedConfig: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        compressionLevel: 3,  // Good balance
        minCompressionSize: 64,  // Standard threshold
        maxCompressionSize: 10 * 1024 * 1024  // 10MB limit
    };

    const configs: Array<[string, CompressionConfiguration]> = [
        ["High Performance", highPerformanceConfig],
        ["High Compression", highCompressionConfig],
        ["Balanced", balancedConfig]
    ];

    const testData = "The quick brown fox jumps over the lazy dog. ".repeat(100);  // ~4.3KB

    for (const [configName, config] of configs) {
        Logger.log("info", "compression_example", `Testing ${configName} configuration`);

        const client = await createClientWithCompression(undefined, config) as GlideClient;

        try {
            // Measure compression performance
            const startSetTime = Date.now();
            await client.set(`test:${configName.toLowerCase().replace(' ', '_')}`, testData);
            const setTime = Date.now() - startSetTime;

            const startGetTime = Date.now();
            const retrieved = await client.get(`test:${configName.toLowerCase().replace(' ', '_')}`);
            const getTime = Date.now() - startGetTime;

            Logger.log("info", "compression_example",
                `  Set time: ${setTime}ms, Get time: ${getTime}ms`);
            Logger.log("info", "compression_example",
                `  Data integrity: ${retrieved?.toString() === testData}`);

        } finally {
            client.close();
        }
    }
}

/**
 * Demonstrates compression with batch operations (pipelines and transactions).
 */
async function batchOperationsExample(): Promise<void> {
    Logger.log("info", "compression_example", "=== Batch Operations with Compression ===");

    const compressionConfig: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        minCompressionSize: 32  // Lower threshold for demo
    };

    const client = await createClientWithCompression(undefined, compressionConfig) as GlideClient;

    try {
        // Pipeline example
        Logger.log("info", "compression_example", "Testing pipeline with compression");

        const pipelineData: Record<string, string> = {
            "user:1": JSON.stringify({ name: "Alice", data: "A".repeat(500) }),
            "user:2": JSON.stringify({ name: "Bob", data: "B".repeat(500) }),
            "user:3": JSON.stringify({ name: "Charlie", data: "C".repeat(500) })
        };

        // Use pipeline to set multiple values (all will be compressed)
        const pipeline = client.createPipeline();
        for (const [key, value] of Object.entries(pipelineData)) {
            pipeline.set(key, value);
        }
        pipeline.mget(Object.keys(pipelineData));
        const results = await client.exec(pipeline);

        Logger.log("info", "compression_example", `Pipeline executed, got ${results.length} results`);

        // The last result is from MGET - verify decompression worked
        const mgetResults = results[results.length - 1] as (string | null)[];
        let index = 0;
        for (const [key, originalValue] of Object.entries(pipelineData)) {
            const retrievedValue = mgetResults[index];
            const matches = retrievedValue === originalValue;
            Logger.log("info", "compression_example", `  ${key}: ${matches}`);
            index++;
        }

        // Transaction example
        Logger.log("info", "compression_example", "Testing transaction with compression");

        const transaction = client.createTransaction();
        transaction.set("counter:compressed", JSON.stringify({ count: 0, data: "x".repeat(200) }));
        transaction.get("counter:compressed");
        transaction.set("counter:compressed", JSON.stringify({ count: 1, data: "x".repeat(200) }));
        transaction.get("counter:compressed");
        const txResults = await client.exec(transaction);

        Logger.log("info", "compression_example", `Transaction executed, got ${txResults.length} results`);

        // Verify the final counter value
        const finalData = JSON.parse(txResults[txResults.length - 1] as string);
        Logger.log("info", "compression_example", `Final counter value: ${finalData.count}`);

    } finally {
        client.close();
    }
}

/**
 * Demonstrates compatibility between compression-enabled and disabled clients.
 */
async function mixedClientScenario(): Promise<void> {
    Logger.log("info", "compression_example", "=== Mixed Client Scenario ===");

    // Client with compression enabled
    const compressionConfig: CompressionConfiguration = { enabled: true };
    const compressedClient = await createClientWithCompression(undefined, compressionConfig) as GlideClient;

    // Client with compression disabled
    const uncompressedClient = await createClientWithCompression(
        undefined,
        { enabled: false }
    ) as GlideClient;

    try {
        const testData = "This is test data that will be compressed. ".repeat(50);

        // Store data with compression-enabled client
        await compressedClient.set("mixed:test", testData);
        Logger.log("info", "compression_example", "Data stored with compression-enabled client");

        // Read with compression-enabled client (automatic decompression)
        const compressedRead = await compressedClient.get("mixed:test");
        Logger.log("info", "compression_example",
            `Compression-enabled client read: ${compressedRead?.toString() === testData}`);

        // Read with compression-disabled client (gets raw compressed data)
        const uncompressedRead = await uncompressedClient.get("mixed:test");
        Logger.log("info", "compression_example",
            `Compression-disabled client read raw data size: ${uncompressedRead?.toString().length || 0} bytes`);
        Logger.log("info", "compression_example",
            `Raw data is different from original: ${uncompressedRead?.toString() !== testData}`);

        // Store uncompressed data
        await uncompressedClient.set("mixed:uncompressed", testData);
        Logger.log("info", "compression_example", "Data stored with compression-disabled client");

        // Read uncompressed data with both clients
        const compressedReadUncomp = await compressedClient.get("mixed:uncompressed");
        const uncompressedReadUncomp = await uncompressedClient.get("mixed:uncompressed");

        Logger.log("info", "compression_example",
            `Both clients read uncompressed data correctly: ${compressedReadUncomp?.toString() === testData &&
            uncompressedReadUncomp?.toString() === testData
            }`);

    } finally {
        compressedClient.close();
        uncompressedClient.close();
    }
}

/**
 * Compares performance with and without compression.
 */
async function performanceComparison(): Promise<void> {
    Logger.log("info", "compression_example", "=== Performance Comparison ===");

    // Test data of different types
    const testCases: Array<[string, string]> = [
        ["Small JSON", JSON.stringify({ id: 1, name: "test" })],
        ["Large JSON", JSON.stringify({ id: 1, data: "x".repeat(2000), metadata: { created: "2024-01-01" } })],
        ["Repetitive Text", "Hello World! ".repeat(200)],
        ["Random-like Data", Array.from({ length: 1000 }, (_, i) => String.fromCharCode(65 + (i % 26))).join("")]
    ];

    const configs: Array<[string, CompressionConfiguration]> = [
        ["No Compression", { enabled: false }],
        ["With Compression", { enabled: true, minCompressionSize: 10 }]
    ];

    for (const [testName, testData] of testCases) {
        Logger.log("info", "compression_example", `Testing: ${testName} (${testData.length} bytes)`);

        for (const [configName, config] of configs) {
            const client = await createClientWithCompression(undefined, config) as GlideClient;

            try {
                // Measure set performance
                const startSetTime = Date.now();
                await client.set(`perf:${testName.toLowerCase().replace(' ', '_')}`, testData);
                const setTime = Date.now() - startSetTime;

                // Measure get performance
                const startGetTime = Date.now();
                const retrieved = await client.get(`perf:${testName.toLowerCase().replace(' ', '_')}`);
                const getTime = Date.now() - startGetTime;

                // Verify data integrity
                const dataMatches = retrieved?.toString() === testData;

                Logger.log("info", "compression_example",
                    `  ${configName}: SET ${setTime}ms, GET ${getTime}ms, Integrity: ${dataMatches}`);

            } finally {
                client.close();
            }
        }

        Logger.log("info", "compression_example", "");
    }
}

/**
 * Demonstrates error handling with compression.
 */
async function errorHandlingExample(): Promise<void> {
    Logger.log("info", "compression_example", "=== Error Handling Example ===");

    try {
        // Try to create client with invalid configuration
        const invalidConfig: CompressionConfiguration = {
            enabled: true,
            compressionLevel: 100,  // Invalid level for ZSTD (max is 22)
        };

        const client = await createClientWithCompression(undefined, invalidConfig) as GlideClient;
        client.close();

    } catch (error) {
        Logger.log("info", "compression_example", `Expected configuration error: ${error?.constructor.name}`);
    }

    // Valid configuration with error handling
    const compressionConfig: CompressionConfiguration = { enabled: true };
    const client = await createClientWithCompression(undefined, compressionConfig) as GlideClient;

    try {
        // Normal operation
        await client.set("error:test", "test data");
        const result = await client.get("error:test");
        Logger.log("info", "compression_example", `Normal operation successful: ${result?.toString()}`);

        // Compression errors are handled gracefully by the client
        // (fallback to uncompressed data with warning logs)

    } catch (error) {
        Logger.log("error", "compression_example", `Unexpected error: ${error}`);
    } finally {
        client.close();
    }
}

/**
 * Demonstrates compression with cluster client.
 */
async function clusterCompressionExample(): Promise<void> {
    Logger.log("info", "compression_example", "=== Cluster Compression Example ===");

    const compressionConfig: CompressionConfiguration = {
        enabled: true,
        backend: CompressionBackend.ZSTD,
        minCompressionSize: 32
    };

    try {
        const clusterClient = await createClientWithCompression(
            [{ host: "localhost", port: 7000 }],  // Adjust for your cluster setup
            compressionConfig,
            true
        ) as GlideClusterClient;

        try {
            // Test compression with cluster operations
            const clusterData: Record<string, string> = {
                "cluster:user:1": JSON.stringify({ name: "Alice", region: "us-east", data: "A".repeat(300) }),
                "cluster:user:2": JSON.stringify({ name: "Bob", region: "us-west", data: "B".repeat(300) }),
                "cluster:user:3": JSON.stringify({ name: "Charlie", region: "eu-west", data: "C".repeat(300) })
            };

            // Set data across cluster (values will be compressed)
            for (const [key, value] of Object.entries(clusterData)) {
                await clusterClient.set(key, value);
            }

            Logger.log("info", "compression_example", "Data stored across cluster with compression");

            // Retrieve data (values will be decompressed)
            const retrievedKeys = Object.keys(clusterData);
            const retrievedValues = await clusterClient.mget(retrievedKeys);

            for (let i = 0; i < retrievedKeys.length; i++) {
                const key = retrievedKeys[i];
                const original = clusterData[key];
                const retrieved = retrievedValues[i]?.toString();
                const matches = retrieved === original;
                Logger.log("info", "compression_example", `  ${key}: ${matches}`);
            }

        } finally {
            clusterClient.close();
        }

    } catch (error) {
        Logger.log("warn", "compression_example",
            `Cluster example skipped (cluster not available): ${error}`);
    }
}

/**
 * Main function that runs all compression examples.
 */
async function main(): Promise<void> {
    Logger.setLoggerConfig("info");

    Logger.log("info", "compression_example", "Starting Valkey GLIDE Compression Examples");
    Logger.log("info", "compression_example", "=".repeat(60));

    try {
        await basicCompressionExample();
        await compressionConfigurationExamples();
        await batchOperationsExample();
        await mixedClientScenario();
        await performanceComparison();
        await errorHandlingExample();
        await clusterCompressionExample();

    } catch (error) {
        Logger.log("error", "compression_example", `Example failed: ${error}`);
        throw error;
    }

    Logger.log("info", "compression_example", "=".repeat(60));
    Logger.log("info", "compression_example", "All compression examples completed successfully!");
}

// Run the examples
main().catch(error => {
    console.error("Failed to run compression examples:", error);
    process.exit(1);
});
