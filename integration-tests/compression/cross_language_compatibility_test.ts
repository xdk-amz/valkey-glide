/**
 * Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
 */

import { spawn } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import {
    CompressionBackend,
    CompressionConfiguration,
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
} from "../../node/build-ts";

/**
 * Cross-language compatibility tests for compression feature.
 * 
 * This test suite verifies that data compressed by one language binding
 * can be decompressed by another language binding, ensuring consistent
 * compression format across all supported languages.
 */
class CrossLanguageCompressionTest {
    private testData: Map<string, Buffer>;
    private tempDir: string;
    private serverAddresses: NodeAddress[];

    constructor() {
        this.testData = this.generateTestData();
        this.tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "glide-compression-test-"));
        this.serverAddresses = [{ host: "127.0.0.1", port: 6379 }];
    }

    private generateTestData(): Map<string, Buffer> {
        const data = new Map<string, Buffer>();

        data.set("small_text", Buffer.from("Hello, World!"));
        data.set("medium_text", Buffer.from("This is a medium-sized text that should be compressed.".repeat(10)));
        data.set("large_text", Buffer.from("This is a large text that should definitely be compressed.".repeat(100)));

        // JSON data
        const jsonData = {
            users: Array.from({ length: 100 }, (_, i) => ({
                id: i,
                name: `User ${i}`,
                email: `user${i}@example.com`
            }))
        };
        data.set("json_data", Buffer.from(JSON.stringify(jsonData)));

        // Binary data
        data.set("binary_data", Buffer.from(Array.from({ length: 2560 }, (_, i) => i % 256)));

        // Highly compressible data
        data.set("highly_compressible", Buffer.from("A".repeat(10000)));

        // Unicode text
        data.set("unicode_text", Buffer.from("Hello 世界! 🌍 Здравствуй мир!".repeat(50)));

        // Edge cases
        data.set("empty_data", Buffer.from(""));
        data.set("single_byte", Buffer.from("A"));

        return data;
    }

    async testNodejsToPythonCompression(): Promise<boolean> {
        console.log("Testing Node.js to Python compression compatibility...");

        const compressionConfig: CompressionConfiguration = {
            enabled: true,
            backend: CompressionBackend.ZSTD,
            compressionLevel: 3,
            minCompressionSize: 32,
        };

        const config: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: compressionConfig,
        };

        const client = await GlideClient.createClient(config);

        try {
            // Store compressed data using Node.js client
            const testKeys: string[] = [];
            for (const [dataName, dataValue] of this.testData.entries()) {
                const key = `nodejs_to_python:${dataName}`;
                testKeys.push(key);
                await client.set(key, dataValue);
                console.log(`  Stored ${dataName} (${dataValue.length} bytes) with Node.js client`);
            }

            // Write test keys to file for Python to read
            const keysFile = path.join(this.tempDir, "nodejs_keys.json");
            fs.writeFileSync(keysFile, JSON.stringify(testKeys));

            // Run Python script to read the data
            const pythonScript = this.createPythonReaderScript();
            const result = await this.runPythonScript(pythonScript, [keysFile]);

            if (!result.success) {
                console.log(`Python script failed: ${result.stderr}`);
                return false;
            }

            // Parse results
            const results = JSON.parse(result.stdout);
            let successCount = 0;

            for (const [key, expectedData] of Array.from(this.testData.entries()).map(([name, data]) => [`nodejs_to_python:${name}`, data])) {
                if (key in results) {
                    const receivedData = Buffer.from(results[key].data);
                    if (receivedData.equals(expectedData)) {
                        successCount++;
                        console.log(`  ✓ ${key}: Data matches`);
                    } else {
                        console.log(`  ✗ ${key}: Data mismatch (expected ${expectedData.length}, got ${receivedData.length})`);
                    }
                } else {
                    console.log(`  ✗ ${key}: Key not found in results`);
                }
            }

            console.log(`Node.js to Python: ${successCount}/${testKeys.length} tests passed`);
            return successCount === testKeys.length;

        } finally {
            client.close();
        }
    }

    async testPythonToNodejsCompression(): Promise<boolean> {
        console.log("Testing Python to Node.js compression compatibility...");

        // Create Python script to store compressed data
        const pythonScript = this.createPythonWriterScript();
        const testDataFile = path.join(this.tempDir, "test_data.json");

        // Write test data to file for Python to use
        const serializableData: { [key: string]: number[] } = {};
        for (const [name, data] of this.testData.entries()) {
            serializableData[name] = Array.from(data);
        }
        fs.writeFileSync(testDataFile, JSON.stringify(serializableData));

        // Run Python script to store the data
        const result = await this.runPythonScript(pythonScript, [testDataFile]);

        if (!result.success) {
            console.log(`Python script failed: ${result.stderr}`);
            return false;
        }

        // Parse the keys that were stored
        const storedKeys = JSON.parse(result.stdout);

        // Create Node.js client with compression enabled to read the data
        const compressionConfig: CompressionConfiguration = {
            enabled: true,
            backend: CompressionBackend.ZSTD,
            compressionLevel: 3,
            minCompressionSize: 32,
        };

        const config: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: compressionConfig,
        };

        const client = await GlideClient.createClient(config);

        try {
            let successCount = 0;

            for (const [dataName, expectedData] of this.testData.entries()) {
                const key = `python_to_nodejs:${dataName}`;
                if (storedKeys.includes(key)) {
                    const receivedData = await client.get(key);
                    if (receivedData && Buffer.from(receivedData).equals(expectedData)) {
                        successCount++;
                        console.log(`  ✓ ${key}: Data matches`);
                    } else {
                        console.log(`  ✗ ${key}: Data mismatch (expected ${expectedData.length}, got ${receivedData ? receivedData.length : 0})`);
                    }
                } else {
                    console.log(`  ✗ ${key}: Key not stored by Python`);
                }
            }

            console.log(`Python to Node.js: ${successCount}/${this.testData.size} tests passed`);
            return successCount === this.testData.size;

        } finally {
            client.close();
        }
    }

    async testCompressionFormatConsistency(): Promise<boolean> {
        console.log("Testing compression format consistency...");

        const compressionConfig: CompressionConfiguration = {
            enabled: true,
            backend: CompressionBackend.ZSTD,
            compressionLevel: 3,
            minCompressionSize: 32,
        };

        const config: GlideClientConfiguration = {
            addresses: this.serverAddresses,
            compression: compressionConfig,
        };

        const testValue = Buffer.from("This is a test value for compression format consistency".repeat(20));

        const client = await GlideClient.createClient(config);

        try {
            // Store the value with Node.js client
            const key = "format_test:nodejs";
            await client.set(key, testValue);

            // Read back the value
            const retrievedValue = await client.get(key);

            if (retrievedValue && Buffer.from(retrievedValue).equals(testValue)) {
                console.log("  ✓ Node.js: Format consistency verified");
                return true;
            } else {
                console.log("  ✗ Node.js: Format inconsistency detected");
                return false;
            }

        } finally {
            client.close();
        }
    }

    private createPythonReaderScript(): string {
        const scriptPath = path.join(this.tempDir, "python_reader.py");
        const scriptContent = `
import asyncio
import json
import sys
import os

# Add the Python client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../python"))

from glide import GlideClient
from glide.config import (
    CompressionBackend,
    CompressionConfiguration,
    GlideClientConfiguration,
    NodeAddress,
)

async def read_compressed_data():
    keys_file = sys.argv[1]
    with open(keys_file, 'r') as f:
        keys = json.load(f)
    
    config = GlideClientConfiguration(
        addresses=[NodeAddress("127.0.0.1", 6379)],
        compression=CompressionConfiguration(
            enabled=True,
            backend=CompressionBackend.ZSTD,
            compression_level=3,
            min_compression_size=32,
        )
    )
    
    client = await GlideClient.create(config)
    
    results = {}
    
    try:
        for key in keys:
            value = await client.get(key)
            if value is not None:
                results[key] = {
                    "data": list(value),
                    "length": len(value)
                }
        
        print(json.dumps(results))
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(read_compressed_data())
`;

        fs.writeFileSync(scriptPath, scriptContent);
        return scriptPath;
    }

    private createPythonWriterScript(): string {
        const scriptPath = path.join(this.tempDir, "python_writer.py");
        const scriptContent = `
import asyncio
import json
import sys
import os

# Add the Python client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../python"))

from glide import GlideClient
from glide.config import (
    CompressionBackend,
    CompressionConfiguration,
    GlideClientConfiguration,
    NodeAddress,
)

async def write_compressed_data():
    data_file = sys.argv[1]
    with open(data_file, 'r') as f:
        test_data = json.load(f)
    
    config = GlideClientConfiguration(
        addresses=[NodeAddress("127.0.0.1", 6379)],
        compression=CompressionConfiguration(
            enabled=True,
            backend=CompressionBackend.ZSTD,
            compression_level=3,
            min_compression_size=32,
        )
    )
    
    client = await GlideClient.create(config)
    
    stored_keys = []
    
    try:
        for data_name, data_array in test_data.items():
            key = f"python_to_nodejs:{data_name}"
            value = bytes(data_array)
            await client.set(key, value)
            stored_keys.append(key)
        
        print(json.dumps(stored_keys))
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(write_compressed_data())
`;

        fs.writeFileSync(scriptPath, scriptContent);
        return scriptPath;
    }

    private async runPythonScript(scriptPath: string, args: string[]): Promise<{ success: boolean; stdout: string; stderr: string }> {
        return new Promise((resolve) => {
            const process = spawn("python3", [scriptPath, ...args], {
                cwd: path.dirname(scriptPath),
            });

            let stdout = "";
            let stderr = "";

            process.stdout.on("data", (data) => {
                stdout += data.toString();
            });

            process.stderr.on("data", (data) => {
                stderr += data.toString();
            });

            process.on("close", (code) => {
                resolve({
                    success: code === 0,
                    stdout: stdout.trim(),
                    stderr: stderr.trim(),
                });
            });
        });
    }

    async runAllTests(): Promise<boolean> {
        console.log("Starting cross-language compression compatibility tests...");

        const tests = [
            () => this.testNodejsToPythonCompression(),
            () => this.testPythonToNodejsCompression(),
            () => this.testCompressionFormatConsistency(),
        ];

        const results: boolean[] = [];
        for (const test of tests) {
            try {
                const result = await test();
                results.push(result);
            } catch (error) {
                console.log(`Test ${test.name} failed with exception: ${error}`);
                results.push(false);
            }
        }

        const passed = results.filter(r => r).length;
        const total = results.length;

        console.log(`\nCross-language compatibility tests: ${passed}/${total} passed`);
        return passed === total;
    }

    cleanup(): void {
        // Clean up temporary directory
        if (fs.existsSync(this.tempDir)) {
            fs.rmSync(this.tempDir, { recursive: true, force: true });
        }
    }
}

// Main test runner
async function main(): Promise<void> {
    const testSuite = new CrossLanguageCompressionTest();

    try {
        const success = await testSuite.runAllTests();
        process.exit(success ? 0 : 1);
    } catch (error) {
        console.error(`Test suite failed: ${error}`);
        process.exit(1);
    } finally {
        testSuite.cleanup();
    }
}

if (require.main === module) {
    main();
}

export { CrossLanguageCompressionTest };
