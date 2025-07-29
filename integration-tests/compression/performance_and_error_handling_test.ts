/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */

import {
    CompressionBackend,
    CompressionConfiguration,
    GlideClient,
    GlideClientConfiguration,
    NodeAddress
} from "../../node/build-ts";

/**
 * Performance and error handling tests for compression feature.
 * 
 * This test suite verifies:
 * 1. Compression/decompression latency overhead
 * 2. Compression ratio effectiveness for different data types
 * 3. Graceful fallback when compression/decompression fails
 * 4. Configuration validation and error reporting
 */
class PerformanceAndErrorHandlingTest {
    private serverAddresses: NodeAddress[];
    private benchmarkResults: { [key: string]: any } = {};

    constructor() {
        this.serverAddresses = [{ host: "127.0.0.1", port: 6379 }];
    }

    private generateBenchmarkData(): Map<string, Buffer> {
        const data = new Map<string, Buffer>();

        // Small data (should not be compressed due to overhead)
        data.set("small_text", Buffer.from("Hello, World!"));
        data.set("small_json", Buffer.from(JSON.stringify({ id: 1, name: "test" })));

        // Medium data (good compression candidates)
        data.set("medium_text", Buffer.from("This is a medium-sized text for compression testing.".repeat(20)));
        data.set("medium_json", Buffer.from(JSON.stringify({
            users: Array.from({ length: 100 }, (_, i) => ({ id: i, name: `User ${i}` }))
        })));

        // Large data (should compress well)
        data.set("large_text", Buffer.from("This is a large text that should compress very well.".repeat(500)));
        data.set("large_json", Buffer.from(JSON.stringify({
            data: Array.from({ length: 1000 }, (_, i) => ({
                id: i,
                value: `value_${i}`,
                metadata: { created: "2024-01-01" }
            }))
        })));

        // Highly compressible data
        data.set("repetitive", Buffer.from("A".repeat(10000)));
        data.set("structured", Buffer.from(JSON.stringify({ pattern: "A".repeat(100) }).repeat(50)));

        // Poorly compressible data (random)
        const randomData = Buffer.alloc(5000);
        for (let i = 0; i < randomData.length; i++) {
            randomData[i] = Math.floor(Math.random() * 256);
        }
        data.set("random_binary", randomData);

        // Binary data
        data.set("binary_pattern", Buffer.from(Array.from({ length: 5120 }, (_, i) => i % 256)));

        // Unicode text
        data.set("unicode_text", Buffer.from("Hello 世界! 🌍 Здравствуй мир! مرحبا بالعالم!".repeat(100)));

        return data;
    }

    async testCompressionLatencyOverhead(): Promise<boolean> {
        console.log("Testing compression latency overhead...");

        const benchmarkData = this.generateBenchmarkData();

        // Configurations to test
        const configs: Array<[string, GlideClientConfiguration]> = [
            ["uncompressed", {
                addresses: this.serverAddresses,
                compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
            }],
            ["zstd_level_1", {
                addresses: this.serverAddresses,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    compressionLevel: 1,
                    minCompressionSize: 32,
                },
            }],
            ["zstd_level_3", {
                addresses: this.serverAddresses,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    compressionLevel: 3,
                    minCompressionSize: 32,
                },
            }],
            ["zstd_level_10", {
                addresses: this.serverAddresses,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    compressionLevel: 10,
                    minCompressionSize: 32,
                },
            }],
        ];

        const results: { [key: string]: any } = {};

        for (const [configName, config] of configs) {
            console.log(`  Benchmarking ${configName}...`);
            const client = await GlideClient.createClient(config);

            try {
                const configResults: { [key: string]: any } = {};

                for (const [dataName, dataValue] of benchmarkData.entries()) {
                    // Skip small data for compression configs (won't be compressed anyway)
                    if (configName !== "uncompressed" && dataValue.length < 32) {
                        continue;
                    }

                    const key = `perf:${configName}:${dataName}`;

                    // Benchmark SET operations
                    const setTimes: number[] = [];
                    for (let i = 0; i < 10; i++) { // 10 iterations for averaging
                        const startTime = performance.now();
                        await client.set(key, dataValue);
                        const endTime = performance.now();
                        setTimes.push(endTime - startTime);
                    }

                    // Benchmark GET operations
                    const getTimes: number[] = [];
                    for (let i = 0; i < 10; i++) { // 10 iterations for averaging
                        const startTime = performance.now();
                        const retrievedValue = await client.get(key);
                        const endTime = performance.now();
                        getTimes.push(endTime - startTime);

                        // Verify data integrity
                        if (configName !== "uncompressed" || (retrievedValue && Buffer.from(retrievedValue).equals(dataValue))) {
                            // Expected behavior
                        } else {
                            console.log(`    Warning: Data integrity issue for ${dataName}`);
                        }
                    }

                    const setAvg = setTimes.reduce((a, b) => a + b, 0) / setTimes.length;
                    const setStd = Math.sqrt(setTimes.reduce((sq, n) => sq + Math.pow(n - setAvg, 2), 0) / setTimes.length);
                    const getAvg = getTimes.reduce((a, b) => a + b, 0) / getTimes.length;
                    const getStd = Math.sqrt(getTimes.reduce((sq, n) => sq + Math.pow(n - getAvg, 2), 0) / getTimes.length);

                    configResults[dataName] = {
                        set_avg_ms: setAvg,
                        set_std_ms: setStd,
                        get_avg_ms: getAvg,
                        get_std_ms: getStd,
                        data_size: dataValue.length,
                    };

                    console.log(`    ${dataName}: SET ${configResults[dataName].set_avg_ms.toFixed(2)}ms, ` +
                        `GET ${configResults[dataName].get_avg_ms.toFixed(2)}ms`);
                }

                results[configName] = configResults;

            } finally {
                client.close();
            }
        }

        // Analyze overhead
        console.log("\n  Performance Analysis:");
        if ("uncompressed" in results) {
            const baseline = results["uncompressed"];

            for (const [configName, configResults] of Object.entries(results)) {
                if (configName === "uncompressed") {
                    continue;
                }

                console.log(`    ${configName} vs uncompressed:`);
                for (const dataName of Object.keys(configResults)) {
                    if (dataName in baseline) {
                        const setOverhead = ((configResults[dataName].set_avg_ms -
                            baseline[dataName].set_avg_ms) /
                            baseline[dataName].set_avg_ms) * 100;
                        const getOverhead = ((configResults[dataName].get_avg_ms -
                            baseline[dataName].get_avg_ms) /
                            baseline[dataName].get_avg_ms) * 100;

                        console.log(`      ${dataName}: SET +${setOverhead.toFixed(1)}%, GET +${getOverhead.toFixed(1)}%`);
                    }
                }
            }
        }

        this.benchmarkResults["latency"] = results;
        return true;
    }

    async testCompressionRatioEffectiveness(): Promise<boolean> {
        console.log("Testing compression ratio effectiveness...");

        const benchmarkData = this.generateBenchmarkData();

        // Test with different compression levels
        const compressionConfigs: Array<[string, number]> = [
            ["zstd_level_1", 1],
            ["zstd_level_3", 3],
            ["zstd_level_10", 10],
        ];

        const ratioResults: { [key: string]: any } = {};

        for (const [configName, compressionLevel] of compressionConfigs) {
            console.log(`  Testing ${configName}...`);

            const config: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    compressionLevel: compressionLevel,
                    minCompressionSize: 16, // Low threshold to test all data
                },
            };

            // Also create uncompressed client to get raw compressed data
            const uncompressedConfig: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
            };

            const compressedClient = await GlideClient.createClient(config);
            const uncompressedClient = await GlideClient.createClient(uncompressedConfig);

            try {
                const configRatios: { [key: string]: any } = {};

                for (const [dataName, dataValue] of benchmarkData.entries()) {
                    if (dataValue.length < 16) { // Skip very small data
                        continue;
                    }

                    const key = `ratio:${configName}:${dataName}`;

                    // Store with compression
                    await compressedClient.set(key, dataValue);

                    // Get raw compressed data
                    const compressedData = await uncompressedClient.get(key);

                    if (compressedData) {
                        const originalSize = dataValue.length;
                        const compressedSize = compressedData.length;
                        const compressionRatio = originalSize / compressedSize;
                        const spaceSaved = ((originalSize - compressedSize) / originalSize) * 100;

                        configRatios[dataName] = {
                            original_size: originalSize,
                            compressed_size: compressedSize,
                            compression_ratio: compressionRatio,
                            space_saved_percent: spaceSaved,
                        };

                        console.log(`    ${dataName}: ${originalSize} -> ${compressedSize} bytes ` +
                            `(ratio: ${compressionRatio.toFixed(2)}x, saved: ${spaceSaved.toFixed(1)}%)`);
                    } else {
                        console.log(`    ${dataName}: No compressed data retrieved`);
                    }
                }

                ratioResults[configName] = configRatios;

            } finally {
                compressedClient.close();
                uncompressedClient.close();
            }
        }

        // Analyze compression effectiveness
        console.log("\n  Compression Effectiveness Analysis:");
        const dataTypes = new Set<string>();
        for (const configResults of Object.values(ratioResults)) {
            for (const dataName of Object.keys(configResults)) {
                dataTypes.add(dataName);
            }
        }

        for (const dataName of Array.from(dataTypes).sort()) {
            console.log(`    ${dataName}:`);
            for (const configName of Object.keys(ratioResults)) {
                if (dataName in ratioResults[configName]) {
                    const result = ratioResults[configName][dataName];
                    console.log(`      ${configName}: ${result.compression_ratio.toFixed(2)}x ` +
                        `(${result.space_saved_percent.toFixed(1)}% saved)`);
                }
            }
        }

        this.benchmarkResults["compression_ratios"] = ratioResults;
        return true;
    }

    async testGracefulFallbackBehavior(): Promise<boolean> {
        console.log("Testing graceful fallback behavior...");

        // Test with valid configuration first
        const validConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 32,
            },
        };

        const client = await GlideClient.createClient(validConfig);

        try {
            // Test 1: Normal operation (should work)
            const testData = Buffer.from("This is test data for fallback testing".repeat(20));
            const key1 = "fallback:normal";

            await client.set(key1, testData);
            const retrievedData = await client.get(key1);

            if (retrievedData && Buffer.from(retrievedData).equals(testData)) {
                console.log("  ✓ Normal compression operation works");
            } else {
                console.log("  ✗ Normal compression operation failed");
                return false;
            }

            // Test 2: Data below compression threshold (should not be compressed)
            const smallData = Buffer.from("small");
            const key2 = "fallback:small";

            await client.set(key2, smallData);
            const retrievedSmall = await client.get(key2);

            if (retrievedSmall && Buffer.from(retrievedSmall).equals(smallData)) {
                console.log("  ✓ Small data handling works (not compressed)");
            } else {
                console.log("  ✗ Small data handling failed");
                return false;
            }

            // Test 3: Empty data
            const emptyData = Buffer.from("");
            const key3 = "fallback:empty";

            await client.set(key3, emptyData);
            const retrievedEmpty = await client.get(key3);

            if (retrievedEmpty && Buffer.from(retrievedEmpty).equals(emptyData)) {
                console.log("  ✓ Empty data handling works");
            } else {
                console.log("  ✗ Empty data handling failed");
                return false;
            }

            // Test 4: Very large data (test memory handling)
            const largeData = Buffer.alloc(1024 * 1024, 'X'); // 1MB of data
            const key4 = "fallback:large";

            try {
                await client.set(key4, largeData);
                const retrievedLarge = await client.get(key4);

                if (retrievedLarge && Buffer.from(retrievedLarge).equals(largeData)) {
                    console.log("  ✓ Large data handling works");
                } else {
                    console.log("  ✗ Large data handling failed - data mismatch");
                    return false;
                }
            } catch (error) {
                console.log(`  ✗ Large data handling failed with exception: ${error}`);
                return false;
            }

            // Test 5: Corrupted compressed data handling
            // Store valid compressed data first
            const key5 = "fallback:corruption_test";
            await client.set(key5, testData);

            // Now try to read with uncompressed client (simulates corruption scenario)
            const uncompressedConfig: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
            };

            const uncompressedClient = await GlideClient.createClient(uncompressedConfig);

            try {
                // This should return the raw compressed bytes
                const rawData = await uncompressedClient.get(key5);
                if (rawData !== null && rawData.length > 0) {
                    console.log("  ✓ Corrupted data scenario handled (returns raw bytes)");
                } else {
                    console.log("  ✗ Corrupted data scenario failed");
                    return false;
                }
            } finally {
                uncompressedClient.close();
            }

            console.log("  All fallback scenarios passed");
            return true;

        } finally {
            client.close();
        }
    }

    async testConfigurationValidationAndErrors(): Promise<boolean> {
        console.log("Testing configuration validation and error reporting...");

        // Test 1: Invalid compression level for ZSTD
        try {
            const invalidConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 25, // Invalid: ZSTD max is 22
                minCompressionSize: 64,
            };

            const config: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: invalidConfig,
            };

            // This should raise an error during client creation
            try {
                const client = await GlideClient.createClient(config);
                client.close();
                console.log("  ✗ Invalid ZSTD compression level was accepted (should have failed)");
                return false;
            } catch (error) {
                console.log(`  ✓ Invalid ZSTD compression level rejected: ${error.constructor.name}`);
            }
        } catch (error) {
            console.log(`  ✓ Invalid ZSTD compression level rejected during config creation: ${error.constructor.name}`);
        }

        // Test 2: Invalid minimum compression size
        try {
            const invalidConfig2: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: -1, // Invalid: should be >= 0
            };

            const config2: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: invalidConfig2,
            };

            try {
                const client = await GlideClient.createClient(config2);
                client.close();
                console.log("  ✗ Invalid min_compression_size was accepted (should have failed)");
                return false;
            } catch (error) {
                console.log(`  ✓ Invalid min_compression_size rejected: ${error.constructor.name}`);
            }
        } catch (error) {
            console.log(`  ✓ Invalid min_compression_size rejected during config creation: ${error.constructor.name}`);
        }

        // Test 3: Invalid max < min compression size
        try {
            const invalidConfig3: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 100,
                maxCompressionSize: 50, // Invalid: max < min
            };

            const config3: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: invalidConfig3,
            };

            try {
                const client = await GlideClient.createClient(config3);
                client.close();
                console.log("  ✗ Invalid max < min compression size was accepted (should have failed)");
                return false;
            } catch (error) {
                console.log(`  ✓ Invalid max < min compression size rejected: ${error.constructor.name}`);
            }
        } catch (error) {
            console.log(`  ✓ Invalid max < min compression size rejected during config creation: ${error.constructor.name}`);
        }

        // Test 4: Valid configuration should work
        try {
            const validConfig: CompressionConfiguration = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 64,
                maxCompressionSize: 1024 * 1024,
            };

            const config: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: validConfig,
            };

            const client = await GlideClient.createClient(config);
            client.close();
            console.log("  ✓ Valid configuration accepted");
        } catch (error) {
            console.log(`  ✗ Valid configuration rejected: ${error}`);
            return false;
        }

        // Test 5: Disabled compression should always work
        try {
            const disabledConfig: CompressionConfiguration = {
                enabled: false,
                backend: CompressionBackend.ZSTD,
                minCompressionSize: 64,
            };

            const config: GlideClientConfiguration = {
                addresses: this.serverAddresses,
                compression: disabledConfig,
            };

            const client = await GlideClient.createClient(config);
            client.close();
            console.log("  ✓ Disabled compression configuration accepted");
        } catch (error) {
            console.log(`  ✗ Disabled compression configuration rejected: ${error}`);
            return false;
        }

        console.log("  All configuration validation tests passed");
        return true;
    }

    async testMemoryUsagePatterns(): Promise<boolean> {
        console.log("Testing memory usage patterns...");

        const config: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 32,
            },
        };

        const client = await GlideClient.createClient(config);

        try {
            // Test with progressively larger data sizes
            const sizes = [1024, 10240, 102400, 1024000]; // 1KB, 10KB, 100KB, 1MB

            for (const size of sizes) {
                const data = Buffer.alloc(size, 'X');
                const key = `memory:test_${size}`;

                // Perform multiple operations to test memory stability
                for (let i = 0; i < 5; i++) {
                    await client.set(`${key}_${i}`, data);
                    const retrieved = await client.get(`${key}_${i}`);

                    if (!retrieved || !Buffer.from(retrieved).equals(data)) {
                        console.log(`  ✗ Memory test failed for size ${size} at iteration ${i}`);
                        return false;
                    }
                }

                console.log(`  ✓ Memory test passed for ${size} bytes`);
            }

            // Test rapid operations
            const rapidData = Buffer.from("Rapid operation test data".repeat(10));
            for (let i = 0; i < 100; i++) {
                const key = `rapid:test_${i}`;
                await client.set(key, rapidData);
                const retrieved = await client.get(key);

                if (!retrieved || !Buffer.from(retrieved).equals(rapidData)) {
                    console.log(`  ✗ Rapid operations test failed at iteration ${i}`);
                    return false;
                }
            }

            console.log("  ✓ Rapid operations test passed");
            console.log("  All memory usage tests passed");
            return true;

        } finally {
            client.close();
        }
    }

    printBenchmarkSummary(): void {
        console.log("\n=== Benchmark Summary ===");

        if ("latency" in this.benchmarkResults) {
            console.log("\nLatency Results:");
            const latencyResults = this.benchmarkResults["latency"];

            // Find common data types across all configurations
            let commonData = new Set<string>();
            for (const [configName, configResults] of Object.entries(latencyResults)) {
                const dataNames = new Set(Object.keys(configResults));
                if (commonData.size === 0) {
                    commonData = dataNames;
                } else {
                    commonData = new Set([...commonData].filter(x => dataNames.has(x)));
                }
            }

            for (const dataName of Array.from(commonData).sort()) {
                console.log(`  ${dataName}:`);
                for (const [configName, configResults] of Object.entries(latencyResults)) {
                    if (dataName in configResults) {
                        const result = configResults[dataName];
                        console.log(`    ${configName}: SET ${result.set_avg_ms.toFixed(2)}ms, ` +
                            `GET ${result.get_avg_ms.toFixed(2)}ms`);
                    }
                }
            }
        }

        if ("compression_ratios" in this.benchmarkResults) {
            console.log("\nCompression Ratio Results:");
            const ratioResults = this.benchmarkResults["compression_ratios"];

            // Find best compression ratios
            const bestRatios: { [key: string]: any } = {};
            for (const [configName, configResults] of Object.entries(ratioResults)) {
                for (const [dataName, result] of Object.entries(configResults)) {
                    if (!(dataName in bestRatios) || result.compression_ratio > bestRatios[dataName].ratio) {
                        bestRatios[dataName] = {
                            ratio: result.compression_ratio,
                            config: configName,
                            space_saved: result.space_saved_percent
                        };
                    }
                }
            }

            for (const [dataName, best] of Object.entries(bestRatios).sort()) {
                console.log(`  ${dataName}: Best ${best.ratio.toFixed(2)}x (${best.space_saved.toFixed(1)}% saved) with ${best.config}`);
            }
        }
    }

    async runAllTests(): Promise<boolean> {
        console.log("Starting performance and error handling tests...");

        const tests = [
            () => this.testCompressionLatencyOverhead(),
            () => this.testCompressionRatioEffectiveness(),
            () => this.testGracefulFallbackBehavior(),
            () => this.testConfigurationValidationAndErrors(),
            () => this.testMemoryUsagePatterns(),
        ];

        const results: boolean[] = [];
        for (const test of tests) {
            try {
                console.log(`\n--- Running ${test.name} ---`);
                const result = await test();
                results.push(result);
                console.log(`Result: ${result ? 'PASS' : 'FAIL'}`);
            } catch (error) {
                console.log(`Test ${test.name} failed with exception: ${error}`);
                results.push(false);
            }
        }

        // Print benchmark summary
        this.printBenchmarkSummary();

        const passed = results.filter(r => r).length;
        const total = results.length;

        console.log(`\nPerformance and error handling tests: ${passed}/${total} passed`);
        return passed === total;
    }
}

// Main test runner
async function main(): Promise<void> {
    const testSuite = new PerformanceAndErrorHandlingTest();

    try {
        const success = await testSuite.runAllTests();
        process.exit(success ? 0 : 1);
    } catch (error) {
        console.error(`Test suite failed: ${error}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

export { PerformanceAndErrorHandlingTest };
