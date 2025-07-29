/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */

import {
    CompressionBackend,
    GlideClient,
    GlideClientConfiguration,
    NodeAddress
} from "../../node/build-ts";

/**
 * Backward compatibility tests for compression feature.
 * 
 * This test suite verifies that:
 * 1. Compression-enabled clients can read uncompressed data
 * 2. Compression-disabled clients can read compressed data
 * 3. No data corruption occurs in mixed-client scenarios
 * 4. Gradual migration from uncompressed to compressed is supported
 */
class BackwardCompatibilityTest {
    private testData: Map<string, Buffer>;
    private serverAddresses: NodeAddress[];

    constructor() {
        this.testData = this.generateTestData();
        this.serverAddresses = [{ host: "127.0.0.1", port: 6379 }];
    }

    private generateTestData(): Map<string, Buffer> {
        const data = new Map<string, Buffer>();

        data.set("small_text", Buffer.from("Hello, World!"));
        data.set("medium_text", Buffer.from("This is a medium-sized text for compatibility testing.".repeat(10)));
        data.set("large_text", Buffer.from("This is a large text that should be handled correctly in mixed scenarios.".repeat(100)));

        // JSON data
        const jsonData = {
            compatibility: "test",
            data: Array.from({ length: 50 }, (_, i) => ({ id: i, value: `item_${i}` }))
        };
        data.set("json_data", Buffer.from(JSON.stringify(jsonData)));

        // Binary data
        data.set("binary_data", Buffer.from(Array.from({ length: 1280 }, (_, i) => i % 256)));

        // Unicode text
        data.set("unicode_text", Buffer.from("Backward compatibility test: 世界 🌍 мир".repeat(20)));

        // Highly compressible data
        data.set("highly_compressible", Buffer.from("A".repeat(5000)));

        // Edge cases
        data.set("empty_data", Buffer.from(""));
        data.set("single_char", Buffer.from("X"));

        return data;
    }

    async testCompressionEnabledReadsUncompressed(): Promise<boolean> {
        console.log("Testing compression-enabled client reading uncompressed data...");

        // First, store data with compression disabled
        const uncompressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
        };

        const uncompressedClient = await GlideClient.createClient(uncompressedConfig);

        try {
            // Store uncompressed data
            const uncompressedKeys: string[] = [];
            for (const [dataName, dataValue] of this.testData.entries()) {
                const key = `uncompressed:${dataName}`;
                uncompressedKeys.push(key);
                await uncompressedClient.set(key, dataValue);
                console.log(`  Stored uncompressed: ${dataName} (${dataValue.length} bytes)`);
            }
        } finally {
            uncompressedClient.close();
        }

        // Now read with compression-enabled client
        const compressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 32,
            },
        };

        const compressedClient = await GlideClient.createClient(compressedConfig);

        try {
            let successCount = 0;

            for (const [dataName, expectedData] of this.testData.entries()) {
                const key = `uncompressed:${dataName}`;
                const retrievedData = await compressedClient.get(key);

                if (retrievedData && Buffer.from(retrievedData).equals(expectedData)) {
                    successCount++;
                    console.log(`  ✓ ${key}: Compression-enabled client correctly read uncompressed data`);
                } else {
                    console.log(`  ✗ ${key}: Data mismatch (expected ${expectedData.length}, got ${retrievedData ? retrievedData.length : 0})`);
                }
            }

            console.log(`Compression-enabled reading uncompressed: ${successCount}/${this.testData.size} tests passed`);
            return successCount === this.testData.size;

        } finally {
            compressedClient.close();
        }
    }

    async testCompressionDisabledReadsCompressed(): Promise<boolean> {
        console.log("Testing compression-disabled client reading compressed data...");

        // First, store data with compression enabled
        const compressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 32,
            },
        };

        const compressedClient = await GlideClient.createClient(compressedConfig);

        try {
            // Store compressed data
            const compressedKeys: string[] = [];
            for (const [dataName, dataValue] of this.testData.entries()) {
                const key = `compressed:${dataName}`;
                compressedKeys.push(key);
                await compressedClient.set(key, dataValue);
                console.log(`  Stored compressed: ${dataName} (${dataValue.length} bytes)`);
            }
        } finally {
            compressedClient.close();
        }

        // Now read with compression-disabled client
        const uncompressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
        };

        const uncompressedClient = await GlideClient.createClient(uncompressedConfig);

        try {
            let successCount = 0;

            for (const [dataName] of this.testData.entries()) {
                const key = `compressed:${dataName}`;
                const retrievedData = await uncompressedClient.get(key);

                // For compression-disabled client reading compressed data,
                // it should get the raw compressed bytes (not the original data)
                if (retrievedData !== null && retrievedData.length > 0) {
                    successCount++;
                    console.log(`  ✓ ${key}: Compression-disabled client retrieved data (${retrievedData.length} bytes)`);

                    // Verify it's actually compressed data by checking for magic header
                    if (retrievedData.length >= 5) { // Magic header is 5 bytes
                        const magicHeader = Buffer.from(retrievedData).subarray(0, 4);
                        if (magicHeader.equals(Buffer.from('GLID'))) {
                            console.log(`    - Confirmed compressed format (magic header present)`);
                        } else {
                            console.log(`    - Data appears uncompressed (no magic header)`);
                        }
                    } else {
                        console.log(`    - Data too small to be compressed`);
                    }
                } else {
                    console.log(`  ✗ ${key}: No data retrieved`);
                }
            }

            console.log(`Compression-disabled reading compressed: ${successCount}/${this.testData.size} tests passed`);
            return successCount === this.testData.size;

        } finally {
            uncompressedClient.close();
        }
    }

    async testMixedClientScenarios(): Promise<boolean> {
        console.log("Testing mixed client scenarios...");

        // Create both types of clients
        const compressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 32,
            },
        };

        const uncompressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
        };

        const compressedClient = await GlideClient.createClient(compressedConfig);
        const uncompressedClient = await GlideClient.createClient(uncompressedConfig);

        try {
            // Test scenario 1: Store with compressed, read with both
            const testValue = Buffer.from("Mixed client scenario test data".repeat(20));
            const key1 = "mixed:compressed_write";

            await compressedClient.set(key1, testValue);

            // Read with compressed client (should get original data)
            const dataFromCompressed = await compressedClient.get(key1);
            // Read with uncompressed client (should get raw compressed bytes)
            const dataFromUncompressed = await uncompressedClient.get(key1);

            const scenario1Success = (
                dataFromCompressed !== null &&
                Buffer.from(dataFromCompressed).equals(testValue) &&
                dataFromUncompressed !== null &&
                dataFromUncompressed.length > 0
            );

            if (scenario1Success) {
                console.log("  ✓ Scenario 1: Compressed write, mixed reads - Success");
            } else {
                console.log("  ✗ Scenario 1: Compressed write, mixed reads - Failed");
            }

            // Test scenario 2: Store with uncompressed, read with both
            const key2 = "mixed:uncompressed_write";

            await uncompressedClient.set(key2, testValue);

            // Read with both clients (both should get original data)
            const dataFromCompressed2 = await compressedClient.get(key2);
            const dataFromUncompressed2 = await uncompressedClient.get(key2);

            const scenario2Success = (
                dataFromCompressed2 !== null &&
                Buffer.from(dataFromCompressed2).equals(testValue) &&
                dataFromUncompressed2 !== null &&
                Buffer.from(dataFromUncompressed2).equals(testValue)
            );

            if (scenario2Success) {
                console.log("  ✓ Scenario 2: Uncompressed write, mixed reads - Success");
            } else {
                console.log("  ✗ Scenario 2: Uncompressed write, mixed reads - Failed");
            }

            // Test scenario 3: Multiple operations with mixed clients
            let operationsSuccess = true;
            for (let i = 0; i < 5; i++) {
                const key = `mixed:operation_${i}`;
                const value = Buffer.from(`Operation ${i} test data`.repeat(10));

                // Alternate between compressed and uncompressed writes
                let writer: string;
                if (i % 2 === 0) {
                    await compressedClient.set(key, value);
                    writer = "compressed";
                } else {
                    await uncompressedClient.set(key, value);
                    writer = "uncompressed";
                }

                // Read with compressed client
                const readValue = await compressedClient.get(key);

                if (writer === "uncompressed" && (readValue === null || !Buffer.from(readValue).equals(value))) {
                    operationsSuccess = false;
                    console.log(`    ✗ Operation ${i}: Failed to read ${writer} data with compressed client`);
                } else if (writer === "compressed" && (readValue === null || !Buffer.from(readValue).equals(value))) {
                    operationsSuccess = false;
                    console.log(`    ✗ Operation ${i}: Failed to read ${writer} data with compressed client`);
                }
            }

            if (operationsSuccess) {
                console.log("  ✓ Scenario 3: Multiple mixed operations - Success");
            } else {
                console.log("  ✗ Scenario 3: Multiple mixed operations - Failed");
            }

            const overallSuccess = scenario1Success && scenario2Success && operationsSuccess;
            console.log(`Mixed client scenarios: ${overallSuccess ? 'All passed' : 'Some failed'}`);
            return overallSuccess;

        } finally {
            compressedClient.close();
            uncompressedClient.close();
        }
    }

    async testGradualMigrationScenario(): Promise<boolean> {
        console.log("Testing gradual migration scenario...");

        // Phase 1: Start with uncompressed client and data
        const uncompressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
        };

        const uncompressedClient = await GlideClient.createClient(uncompressedConfig);

        const migrationData = new Map<string, Buffer>([
            ["user:1", Buffer.from("User 1 profile data".repeat(10))],
            ["user:2", Buffer.from("User 2 profile data".repeat(10))],
            ["config:app", Buffer.from(JSON.stringify({ version: "1.0", features: ["a", "b", "c"] }))],
            ["cache:session:123", Buffer.from("Session data for user 123".repeat(5))],
        ]);

        try {
            // Store initial uncompressed data
            for (const [key, value] of migrationData.entries()) {
                await uncompressedClient.set(key, value);
                console.log(`  Phase 1: Stored uncompressed ${key}`);
            }
        } finally {
            uncompressedClient.close();
        }

        // Phase 2: Enable compression for new client
        const compressedConfig: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: 3,
                minCompressionSize: 32,
            },
        };

        const compressedClient = await GlideClient.createClient(compressedConfig);

        let phase2Success = true;

        try {
            // Verify compressed client can read existing uncompressed data
            for (const [key, expectedValue] of migrationData.entries()) {
                const retrievedValue = await compressedClient.get(key);
                if (retrievedValue === null || !Buffer.from(retrievedValue).equals(expectedValue)) {
                    phase2Success = false;
                    console.log(`  ✗ Phase 2: Failed to read existing data for ${key}`);
                } else {
                    console.log(`  ✓ Phase 2: Successfully read existing data for ${key}`);
                }
            }

            // Add new data with compression enabled
            const newData = new Map<string, Buffer>([
                ["user:3", Buffer.from("User 3 profile data (compressed)".repeat(15))],
                ["cache:session:456", Buffer.from("Session data for user 456 (compressed)".repeat(8))],
                ["analytics:daily", Buffer.from(JSON.stringify({ date: "2024-01-01", events: Array.from({ length: 100 }, (_, i) => i) }))],
            ]);

            for (const [key, value] of newData.entries()) {
                await compressedClient.set(key, value);
                console.log(`  Phase 2: Stored compressed ${key}`);
            }

            // Verify new compressed data can be read
            for (const [key, expectedValue] of newData.entries()) {
                const retrievedValue = await compressedClient.get(key);
                if (retrievedValue === null || !Buffer.from(retrievedValue).equals(expectedValue)) {
                    phase2Success = false;
                    console.log(`  ✗ Phase 2: Failed to read new compressed data for ${key}`);
                } else {
                    console.log(`  ✓ Phase 2: Successfully read new compressed data for ${key}`);
                }
            }

            // Phase 3: Verify mixed data can be accessed by both client types
            const uncompressedClient2 = await GlideClient.createClient(uncompressedConfig);
            const compressedClient2 = await GlideClient.createClient(compressedConfig);

            let phase3Success = true;

            try {
                // Test that uncompressed client can still read original data
                for (const [key, expectedValue] of migrationData.entries()) {
                    const retrievedValue = await uncompressedClient2.get(key);
                    if (retrievedValue === null || !Buffer.from(retrievedValue).equals(expectedValue)) {
                        phase3Success = false;
                        console.log(`  ✗ Phase 3: Uncompressed client failed to read original data for ${key}`);
                    } else {
                        console.log(`  ✓ Phase 3: Uncompressed client read original data for ${key}`);
                    }
                }

                // Test that compressed client can read all data (original + new)
                const allData = new Map([...migrationData, ...newData]);
                for (const [key, expectedValue] of allData.entries()) {
                    const retrievedValue = await compressedClient2.get(key);
                    if (retrievedValue === null || !Buffer.from(retrievedValue).equals(expectedValue)) {
                        phase3Success = false;
                        console.log(`  ✗ Phase 3: Compressed client failed to read data for ${key}`);
                    } else {
                        console.log(`  ✓ Phase 3: Compressed client read data for ${key}`);
                    }
                }

            } finally {
                uncompressedClient2.close();
                compressedClient2.close();
            }

            const overallSuccess = phase2Success && phase3Success;
            console.log(`Gradual migration scenario: ${overallSuccess ? 'Success' : 'Failed'}`);
            return overallSuccess;

        } finally {
            compressedClient.close();
        }
    }

    async testDataIntegrityAcrossConfigurations(): Promise<boolean> {
        console.log("Testing data integrity across compression configurations...");

        // Test with different compression levels
        const configs: Array<[string, GlideClientConfiguration]> = [
            ["disabled", {
                addresses: this.serverAddresses,
                compression: { enabled: false, backend: CompressionBackend.ZSTD, minCompressionSize: 64 },
            }],
            ["zstd_level_1", {
                addresses: this.serverAddresses,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    compressionLevel: 1,
                    minCompressionSize: 16,
                },
            }],
            ["zstd_level_10", {
                addresses: this.serverAddresses,
                compression: {
                    enabled: true,
                    backend: CompressionBackend.ZSTD,
                    compressionLevel: 10,
                    minCompressionSize: 16,
                },
            }],
        ];

        const testValue = Buffer.from("Data integrity test value that should be handled consistently".repeat(25));

        // Store data with each configuration
        for (const [configName, config] of configs) {
            const client = await GlideClient.createClient(config);
            try {
                const key = `integrity:${configName}`;
                await client.set(key, testValue);
                console.log(`  Stored with ${configName} configuration`);
            } finally {
                client.close();
            }
        }

        // Read data with each configuration and verify integrity
        let integritySuccess = true;

        for (const [readerName, readerConfig] of configs) {
            const readerClient = await GlideClient.createClient(readerConfig);
            try {
                for (const [writerName] of configs) {
                    const key = `integrity:${writerName}`;
                    const retrievedValue = await readerClient.get(key);

                    // For disabled compression reading compressed data, we expect raw bytes
                    if (readerName === "disabled" && writerName !== "disabled") {
                        // Should get compressed bytes, not original data
                        if (retrievedValue !== null && retrievedValue.length > 0) {
                            console.log(`  ✓ ${readerName} read ${writerName} data (raw compressed bytes)`);
                        } else {
                            integritySuccess = false;
                            console.log(`  ✗ ${readerName} failed to read ${writerName} data`);
                        }
                    } else {
                        // Should get original data
                        if (retrievedValue !== null && Buffer.from(retrievedValue).equals(testValue)) {
                            console.log(`  ✓ ${readerName} correctly read ${writerName} data`);
                        } else {
                            integritySuccess = false;
                            console.log(`  ✗ ${readerName} failed to read ${writerName} data correctly`);
                        }
                    }
                }
            } finally {
                readerClient.close();
            }
        }

        console.log(`Data integrity test: ${integritySuccess ? 'Success' : 'Failed'}`);
        return integritySuccess;
    }

    async runAllTests(): Promise<boolean> {
        console.log("Starting backward compatibility tests...");

        const tests = [
            () => this.testCompressionEnabledReadsUncompressed(),
            () => this.testCompressionDisabledReadsCompressed(),
            () => this.testMixedClientScenarios(),
            () => this.testGradualMigrationScenario(),
            () => this.testDataIntegrityAcrossConfigurations(),
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

        const passed = results.filter(r => r).length;
        const total = results.length;

        console.log(`\nBackward compatibility tests: ${passed}/${total} passed`);
        return passed === total;
    }
}

// Main test runner
async function main(): Promise<void> {
    const testSuite = new BackwardCompatibilityTest();

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

export { BackwardCompatibilityTest };
