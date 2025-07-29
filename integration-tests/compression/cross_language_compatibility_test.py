#!/usr/bin/env python3
"""
Cross-language compatibility tests for compression feature.

This test suite verifies that data compressed by one language binding
can be decompressed by another language binding, ensuring consistent
compression format across all supported languages.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

import pytest

# Add the Python client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../python"))

from glide import GlideClient, GlideClusterClient
from glide.config import (
    CompressionBackend,
    CompressionConfiguration,
    GlideClientConfiguration,
    GlideClusterClientConfiguration,
    NodeAddress,
)


class CrossLanguageCompressionTest:
    """Test suite for cross-language compression compatibility."""

    def __init__(self):
        self.test_data = self._generate_test_data()
        self.temp_dir = tempfile.mkdtemp()
        self.server_addresses = [NodeAddress("127.0.0.1", 6379)]
        
    def _generate_test_data(self) -> Dict[str, bytes]:
        """Generate various types of test data for compression testing."""
        return {
            "small_text": b"Hello, World!",
            "medium_text": b"This is a medium-sized text that should be compressed." * 10,
            "large_text": b"This is a large text that should definitely be compressed." * 100,
            "json_data": json.dumps({
                "users": [
                    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
                    for i in range(100)
                ]
            }).encode(),
            "binary_data": bytes(range(256)) * 10,
            "highly_compressible": b"AAAAAAAAAA" * 1000,
            "unicode_text": "Hello 世界! 🌍 Здравствуй мир!".encode("utf-8") * 50,
            "empty_data": b"",
            "single_byte": b"A",
        }

    async def test_python_to_nodejs_compression(self):
        """Test that data compressed by Python can be read by Node.js."""
        print("Testing Python to Node.js compression compatibility...")
        
        # Create Python client with compression enabled
        python_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        python_client = await GlideClient.create(python_config)
        
        try:
            # Store compressed data using Python client
            test_keys = []
            for data_name, data_value in self.test_data.items():
                key = f"python_to_nodejs:{data_name}"
                test_keys.append(key)
                await python_client.set(key, data_value)
                print(f"  Stored {data_name} ({len(data_value)} bytes) with Python client")
            
            # Write test keys to file for Node.js to read
            keys_file = os.path.join(self.temp_dir, "python_keys.json")
            with open(keys_file, "w") as f:
                json.dump(test_keys, f)
            
            # Run Node.js script to read the data
            nodejs_script = self._create_nodejs_reader_script()
            result = subprocess.run([
                "node", nodejs_script, keys_file
            ], capture_output=True, text=True, cwd="node")
            
            if result.returncode != 0:
                print(f"Node.js script failed: {result.stderr}")
                return False
            
            # Parse results
            results = json.loads(result.stdout)
            success_count = 0
            
            for key, expected_data in zip(test_keys, self.test_data.values()):
                if key in results:
                    received_data = bytes(results[key]["data"])
                    if received_data == expected_data:
                        success_count += 1
                        print(f"  ✓ {key}: Data matches")
                    else:
                        print(f"  ✗ {key}: Data mismatch (expected {len(expected_data)}, got {len(received_data)})")
                else:
                    print(f"  ✗ {key}: Key not found in results")
            
            print(f"Python to Node.js: {success_count}/{len(test_keys)} tests passed")
            return success_count == len(test_keys)
            
        finally:
            await python_client.close()

    async def test_nodejs_to_python_compression(self):
        """Test that data compressed by Node.js can be read by Python."""
        print("Testing Node.js to Python compression compatibility...")
        
        # Create Node.js script to store compressed data
        nodejs_script = self._create_nodejs_writer_script()
        test_data_file = os.path.join(self.temp_dir, "test_data.json")
        
        # Write test data to file for Node.js to use
        serializable_data = {
            name: list(data) for name, data in self.test_data.items()
        }
        with open(test_data_file, "w") as f:
            json.dump(serializable_data, f)
        
        # Run Node.js script to store the data
        result = subprocess.run([
            "node", nodejs_script, test_data_file
        ], capture_output=True, text=True, cwd="node")
        
        if result.returncode != 0:
            print(f"Node.js script failed: {result.stderr}")
            return False
        
        # Parse the keys that were stored
        stored_keys = json.loads(result.stdout)
        
        # Create Python client with compression enabled to read the data
        python_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        python_client = await GlideClient.create(python_config)
        
        try:
            success_count = 0
            
            for data_name, expected_data in self.test_data.items():
                key = f"nodejs_to_python:{data_name}"
                if key in stored_keys:
                    received_data = await python_client.get(key)
                    if received_data == expected_data:
                        success_count += 1
                        print(f"  ✓ {key}: Data matches")
                    else:
                        print(f"  ✗ {key}: Data mismatch (expected {len(expected_data)}, got {len(received_data) if received_data else 0})")
                else:
                    print(f"  ✗ {key}: Key not stored by Node.js")
            
            print(f"Node.js to Python: {success_count}/{len(self.test_data)} tests passed")
            return success_count == len(self.test_data)
            
        finally:
            await python_client.close()

    async def test_compression_format_consistency(self):
        """Test that compression format is consistent across language bindings."""
        print("Testing compression format consistency...")
        
        # Test with both Python and Node.js clients
        configs = [
            ("python", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(
                    enabled=True,
                    backend=CompressionBackend.ZSTD,
                    compression_level=3,
                    min_compression_size=32,
                )
            )),
        ]
        
        test_value = b"This is a test value for compression format consistency" * 20
        
        for client_name, config in configs:
            client = await GlideClient.create(config)
            
            try:
                # Store the same value with different clients
                key = f"format_test:{client_name}"
                await client.set(key, test_value)
                
                # Read back the value
                retrieved_value = await client.get(key)
                
                if retrieved_value == test_value:
                    print(f"  ✓ {client_name}: Format consistency verified")
                else:
                    print(f"  ✗ {client_name}: Format inconsistency detected")
                    return False
                    
            finally:
                await client.close()
        
        return True

    def _create_nodejs_reader_script(self) -> str:
        """Create a Node.js script to read compressed data."""
        script_path = os.path.join(self.temp_dir, "nodejs_reader.js")
        script_content = '''
const { GlideClient } = require('./build-ts');
const { CompressionBackend } = require('./build-ts');
const fs = require('fs');

async function readCompressedData() {
    const keysFile = process.argv[2];
    const keys = JSON.parse(fs.readFileSync(keysFile, 'utf8'));
    
    const client = await GlideClient.createClient({
        addresses: [{ host: '127.0.0.1', port: 6379 }],
        compression: {
            enabled: true,
            backend: CompressionBackend.ZSTD,
            compressionLevel: 3,
            minCompressionSize: 32,
        }
    });
    
    const results = {};
    
    try {
        for (const key of keys) {
            const value = await client.get(key);
            if (value !== null) {
                results[key] = {
                    data: Array.from(value),
                    length: value.length
                };
            }
        }
        
        console.log(JSON.stringify(results));
    } finally {
        client.close();
    }
}

readCompressedData().catch(console.error);
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return script_path

    def _create_nodejs_writer_script(self) -> str:
        """Create a Node.js script to write compressed data."""
        script_path = os.path.join(self.temp_dir, "nodejs_writer.js")
        script_content = '''
const { GlideClient } = require('./build-ts');
const { CompressionBackend } = require('./build-ts');
const fs = require('fs');

async function writeCompressedData() {
    const dataFile = process.argv[2];
    const testData = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
    
    const client = await GlideClient.createClient({
        addresses: [{ host: '127.0.0.1', port: 6379 }],
        compression: {
            enabled: true,
            backend: CompressionBackend.ZSTD,
            compressionLevel: 3,
            minCompressionSize: 32,
        }
    });
    
    const storedKeys = [];
    
    try {
        for (const [dataName, dataArray] of Object.entries(testData)) {
            const key = `nodejs_to_python:${dataName}`;
            const value = Buffer.from(dataArray);
            await client.set(key, value);
            storedKeys.push(key);
        }
        
        console.log(JSON.stringify(storedKeys));
    } finally {
        client.close();
    }
}

writeCompressedData().catch(console.error);
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return script_path

    async def run_all_tests(self) -> bool:
        """Run all cross-language compatibility tests."""
        print("Starting cross-language compression compatibility tests...")
        
        tests = [
            self.test_python_to_nodejs_compression,
            self.test_nodejs_to_python_compression,
            self.test_compression_format_consistency,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"Test {test.__name__} failed with exception: {e}")
                results.append(False)
        
        passed = sum(results)
        total = len(results)
        
        print(f"\nCross-language compatibility tests: {passed}/{total} passed")
        return passed == total


async def main():
    """Main test runner."""
    test_suite = CrossLanguageCompressionTest()
    
    try:
        success = await test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
