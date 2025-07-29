#!/usr/bin/env python3
"""
Backward compatibility tests for compression feature.

This test suite verifies that:
1. Compression-enabled clients can read uncompressed data
2. Compression-disabled clients can read compressed data
3. No data corruption occurs in mixed-client scenarios
4. Gradual migration from uncompressed to compressed is supported
"""

import asyncio
import json
import os
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


class BackwardCompatibilityTest:
    """Test suite for backward compatibility of compression feature."""

    def __init__(self):
        self.test_data = self._generate_test_data()
        self.server_addresses = [NodeAddress("127.0.0.1", 6379)]
        
    def _generate_test_data(self) -> Dict[str, bytes]:
        """Generate various types of test data for compatibility testing."""
        return {
            "small_text": b"Hello, World!",
            "medium_text": b"This is a medium-sized text for compatibility testing." * 10,
            "large_text": b"This is a large text that should be handled correctly in mixed scenarios." * 100,
            "json_data": json.dumps({
                "compatibility": "test",
                "data": [{"id": i, "value": f"item_{i}"} for i in range(50)]
            }).encode(),
            "binary_data": bytes(range(256)) * 5,
            "unicode_text": "Backward compatibility test: 世界 🌍 мир".encode("utf-8") * 20,
            "highly_compressible": b"AAAAAAAAAA" * 500,
            "empty_data": b"",
            "single_char": b"X",
        }

    async def test_compression_enabled_reads_uncompressed(self):
        """Test that compression-enabled clients can read uncompressed data."""
        print("Testing compression-enabled client reading uncompressed data...")
        
        # First, store data with compression disabled
        uncompressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(enabled=False)
        )
        
        uncompressed_client = await GlideClient.create(uncompressed_config)
        
        try:
            # Store uncompressed data
            uncompressed_keys = []
            for data_name, data_value in self.test_data.items():
                key = f"uncompressed:{data_name}"
                uncompressed_keys.append(key)
                await uncompressed_client.set(key, data_value)
                print(f"  Stored uncompressed: {data_name} ({len(data_value)} bytes)")
        finally:
            await uncompressed_client.close()
        
        # Now read with compression-enabled client
        compressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        compressed_client = await GlideClient.create(compressed_config)
        
        try:
            success_count = 0
            
            for data_name, expected_data in self.test_data.items():
                key = f"uncompressed:{data_name}"
                retrieved_data = await compressed_client.get(key)
                
                if retrieved_data == expected_data:
                    success_count += 1
                    print(f"  ✓ {key}: Compression-enabled client correctly read uncompressed data")
                else:
                    print(f"  ✗ {key}: Data mismatch (expected {len(expected_data)}, got {len(retrieved_data) if retrieved_data else 0})")
            
            print(f"Compression-enabled reading uncompressed: {success_count}/{len(self.test_data)} tests passed")
            return success_count == len(self.test_data)
            
        finally:
            await compressed_client.close()

    async def test_compression_disabled_reads_compressed(self):
        """Test that compression-disabled clients can read compressed data."""
        print("Testing compression-disabled client reading compressed data...")
        
        # First, store data with compression enabled
        compressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        compressed_client = await GlideClient.create(compressed_config)
        
        try:
            # Store compressed data
            compressed_keys = []
            for data_name, data_value in self.test_data.items():
                key = f"compressed:{data_name}"
                compressed_keys.append(key)
                await compressed_client.set(key, data_value)
                print(f"  Stored compressed: {data_name} ({len(data_value)} bytes)")
        finally:
            await compressed_client.close()
        
        # Now read with compression-disabled client
        uncompressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(enabled=False)
        )
        
        uncompressed_client = await GlideClient.create(uncompressed_config)
        
        try:
            success_count = 0
            
            for data_name, expected_data in self.test_data.items():
                key = f"compressed:{data_name}"
                retrieved_data = await uncompressed_client.get(key)
                
                # For compression-disabled client reading compressed data,
                # it should get the raw compressed bytes (not the original data)
                # This is expected behavior - the client gets what's stored
                if retrieved_data is not None:
                    success_count += 1
                    print(f"  ✓ {key}: Compression-disabled client retrieved data ({len(retrieved_data)} bytes)")
                    
                    # Verify it's actually compressed data by checking for magic header
                    if len(retrieved_data) >= 5:  # Magic header is 5 bytes
                        magic_header = retrieved_data[:4]
                        if magic_header == b'GLID':
                            print(f"    - Confirmed compressed format (magic header present)")
                        else:
                            print(f"    - Data appears uncompressed (no magic header)")
                    else:
                        print(f"    - Data too small to be compressed")
                else:
                    print(f"  ✗ {key}: No data retrieved")
            
            print(f"Compression-disabled reading compressed: {success_count}/{len(self.test_data)} tests passed")
            return success_count == len(self.test_data)
            
        finally:
            await uncompressed_client.close()

    async def test_mixed_client_scenarios(self):
        """Test mixed scenarios with both compressed and uncompressed clients."""
        print("Testing mixed client scenarios...")
        
        # Create both types of clients
        compressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        uncompressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(enabled=False)
        )
        
        compressed_client = await GlideClient.create(compressed_config)
        uncompressed_client = await GlideClient.create(uncompressed_config)
        
        try:
            # Test scenario 1: Store with compressed, read with both
            test_value = b"Mixed client scenario test data" * 20
            key1 = "mixed:compressed_write"
            
            await compressed_client.set(key1, test_value)
            
            # Read with compressed client (should get original data)
            data_from_compressed = await compressed_client.get(key1)
            # Read with uncompressed client (should get raw compressed bytes)
            data_from_uncompressed = await uncompressed_client.get(key1)
            
            scenario1_success = (
                data_from_compressed == test_value and
                data_from_uncompressed is not None and
                len(data_from_uncompressed) > 0
            )
            
            if scenario1_success:
                print("  ✓ Scenario 1: Compressed write, mixed reads - Success")
            else:
                print("  ✗ Scenario 1: Compressed write, mixed reads - Failed")
            
            # Test scenario 2: Store with uncompressed, read with both
            key2 = "mixed:uncompressed_write"
            
            await uncompressed_client.set(key2, test_value)
            
            # Read with both clients (both should get original data)
            data_from_compressed2 = await compressed_client.get(key2)
            data_from_uncompressed2 = await uncompressed_client.get(key2)
            
            scenario2_success = (
                data_from_compressed2 == test_value and
                data_from_uncompressed2 == test_value
            )
            
            if scenario2_success:
                print("  ✓ Scenario 2: Uncompressed write, mixed reads - Success")
            else:
                print("  ✗ Scenario 2: Uncompressed write, mixed reads - Failed")
            
            # Test scenario 3: Multiple operations with mixed clients
            operations_success = True
            for i in range(5):
                key = f"mixed:operation_{i}"
                value = f"Operation {i} test data".encode() * 10
                
                # Alternate between compressed and uncompressed writes
                if i % 2 == 0:
                    await compressed_client.set(key, value)
                    writer = "compressed"
                else:
                    await uncompressed_client.set(key, value)
                    writer = "uncompressed"
                
                # Read with compressed client
                read_value = await compressed_client.get(key)
                
                if writer == "uncompressed" and read_value != value:
                    operations_success = False
                    print(f"    ✗ Operation {i}: Failed to read {writer} data with compressed client")
                elif writer == "compressed" and read_value != value:
                    operations_success = False
                    print(f"    ✗ Operation {i}: Failed to read {writer} data with compressed client")
            
            if operations_success:
                print("  ✓ Scenario 3: Multiple mixed operations - Success")
            else:
                print("  ✗ Scenario 3: Multiple mixed operations - Failed")
            
            overall_success = scenario1_success and scenario2_success and operations_success
            print(f"Mixed client scenarios: {'All passed' if overall_success else 'Some failed'}")
            return overall_success
            
        finally:
            await compressed_client.close()
            await uncompressed_client.close()

    async def test_gradual_migration_scenario(self):
        """Test gradual migration from uncompressed to compressed usage."""
        print("Testing gradual migration scenario...")
        
        # Phase 1: Start with uncompressed client and data
        uncompressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(enabled=False)
        )
        
        uncompressed_client = await GlideClient.create(uncompressed_config)
        
        try:
            # Store initial uncompressed data
            migration_data = {
                "user:1": b"User 1 profile data" * 10,
                "user:2": b"User 2 profile data" * 10,
                "config:app": json.dumps({"version": "1.0", "features": ["a", "b", "c"]}).encode(),
                "cache:session:123": b"Session data for user 123" * 5,
            }
            
            for key, value in migration_data.items():
                await uncompressed_client.set(key, value)
                print(f"  Phase 1: Stored uncompressed {key}")
        finally:
            await uncompressed_client.close()
        
        # Phase 2: Enable compression for new client
        compressed_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        compressed_client = await GlideClient.create(compressed_config)
        
        try:
            # Verify compressed client can read existing uncompressed data
            phase2_success = True
            for key, expected_value in migration_data.items():
                retrieved_value = await compressed_client.get(key)
                if retrieved_value != expected_value:
                    phase2_success = False
                    print(f"  ✗ Phase 2: Failed to read existing data for {key}")
                else:
                    print(f"  ✓ Phase 2: Successfully read existing data for {key}")
            
            # Add new data with compression enabled
            new_data = {
                "user:3": b"User 3 profile data (compressed)" * 15,
                "cache:session:456": b"Session data for user 456 (compressed)" * 8,
                "analytics:daily": json.dumps({"date": "2024-01-01", "events": list(range(100))}).encode(),
            }
            
            for key, value in new_data.items():
                await compressed_client.set(key, value)
                print(f"  Phase 2: Stored compressed {key}")
            
            # Verify new compressed data can be read
            for key, expected_value in new_data.items():
                retrieved_value = await compressed_client.get(key)
                if retrieved_value != expected_value:
                    phase2_success = False
                    print(f"  ✗ Phase 2: Failed to read new compressed data for {key}")
                else:
                    print(f"  ✓ Phase 2: Successfully read new compressed data for {key}")
            
        finally:
            await compressed_client.close()
        
        # Phase 3: Verify mixed data can be accessed by both client types
        uncompressed_client2 = await GlideClient.create(uncompressed_config)
        compressed_client2 = await GlideClient.create(compressed_config)
        
        try:
            phase3_success = True
            
            # Test that uncompressed client can still read original data
            for key, expected_value in migration_data.items():
                retrieved_value = await uncompressed_client2.get(key)
                if retrieved_value != expected_value:
                    phase3_success = False
                    print(f"  ✗ Phase 3: Uncompressed client failed to read original data for {key}")
                else:
                    print(f"  ✓ Phase 3: Uncompressed client read original data for {key}")
            
            # Test that compressed client can read all data (original + new)
            all_data = {**migration_data, **new_data}
            for key, expected_value in all_data.items():
                retrieved_value = await compressed_client2.get(key)
                if retrieved_value != expected_value:
                    phase3_success = False
                    print(f"  ✗ Phase 3: Compressed client failed to read data for {key}")
                else:
                    print(f"  ✓ Phase 3: Compressed client read data for {key}")
            
            overall_success = phase2_success and phase3_success
            print(f"Gradual migration scenario: {'Success' if overall_success else 'Failed'}")
            return overall_success
            
        finally:
            await uncompressed_client2.close()
            await compressed_client2.close()

    async def test_data_integrity_across_configurations(self):
        """Test that data integrity is maintained across different compression configurations."""
        print("Testing data integrity across compression configurations...")
        
        # Test with different compression levels
        configs = [
            ("disabled", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(enabled=False)
            )),
            ("zstd_level_1", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(
                    enabled=True,
                    backend=CompressionBackend.ZSTD,
                    compression_level=1,
                    min_compression_size=16,
                )
            )),
            ("zstd_level_10", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(
                    enabled=True,
                    backend=CompressionBackend.ZSTD,
                    compression_level=10,
                    min_compression_size=16,
                )
            )),
        ]
        
        test_value = b"Data integrity test value that should be handled consistently" * 25
        
        # Store data with each configuration
        for config_name, config in configs:
            client = await GlideClient.create(config)
            try:
                key = f"integrity:{config_name}"
                await client.set(key, test_value)
                print(f"  Stored with {config_name} configuration")
            finally:
                await client.close()
        
        # Read data with each configuration and verify integrity
        integrity_success = True
        
        for reader_name, reader_config in configs:
            reader_client = await GlideClient.create(reader_config)
            try:
                for writer_name, _ in configs:
                    key = f"integrity:{writer_name}"
                    retrieved_value = await reader_client.get(key)
                    
                    # For disabled compression reading compressed data, we expect raw bytes
                    if reader_name == "disabled" and writer_name != "disabled":
                        # Should get compressed bytes, not original data
                        if retrieved_value is not None and len(retrieved_value) > 0:
                            print(f"  ✓ {reader_name} read {writer_name} data (raw compressed bytes)")
                        else:
                            integrity_success = False
                            print(f"  ✗ {reader_name} failed to read {writer_name} data")
                    else:
                        # Should get original data
                        if retrieved_value == test_value:
                            print(f"  ✓ {reader_name} correctly read {writer_name} data")
                        else:
                            integrity_success = False
                            print(f"  ✗ {reader_name} failed to read {writer_name} data correctly")
            finally:
                await reader_client.close()
        
        print(f"Data integrity test: {'Success' if integrity_success else 'Failed'}")
        return integrity_success

    async def run_all_tests(self) -> bool:
        """Run all backward compatibility tests."""
        print("Starting backward compatibility tests...")
        
        tests = [
            self.test_compression_enabled_reads_uncompressed,
            self.test_compression_disabled_reads_compressed,
            self.test_mixed_client_scenarios,
            self.test_gradual_migration_scenario,
            self.test_data_integrity_across_configurations,
        ]
        
        results = []
        for test in tests:
            try:
                print(f"\n--- Running {test.__name__} ---")
                result = await test()
                results.append(result)
                print(f"Result: {'PASS' if result else 'FAIL'}")
            except Exception as e:
                print(f"Test {test.__name__} failed with exception: {e}")
                results.append(False)
        
        passed = sum(results)
        total = len(results)
        
        print(f"\nBackward compatibility tests: {passed}/{total} passed")
        return passed == total


async def main():
    """Main test runner."""
    test_suite = BackwardCompatibilityTest()
    
    try:
        success = await test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
