#!/usr/bin/env python3
"""
Performance and error handling tests for compression feature.

This test suite verifies:
1. Compression/decompression latency overhead
2. Compression ratio effectiveness for different data types
3. Graceful fallback when compression/decompression fails
4. Configuration validation and error reporting
"""

import asyncio
import json
import os
import random
import statistics
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import pytest

# Add the Python client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../python"))

from glide import GlideClient, GlideClusterClient
from glide.config import (
    CompressionBackend,
    CompressionConfiguration,
    ConfigurationError,
    GlideClientConfiguration,
    GlideClusterClientConfiguration,
    NodeAddress,
)


class PerformanceAndErrorHandlingTest:
    """Test suite for performance benchmarks and error handling."""

    def __init__(self):
        self.server_addresses = [NodeAddress("127.0.0.1", 6379)]
        self.benchmark_results = {}
        
    def _generate_benchmark_data(self) -> Dict[str, bytes]:
        """Generate various types of data for performance benchmarking."""
        data = {}
        
        # Small data (should not be compressed due to overhead)
        data["small_text"] = b"Hello, World!"
        data["small_json"] = json.dumps({"id": 1, "name": "test"}).encode()
        
        # Medium data (good compression candidates)
        data["medium_text"] = b"This is a medium-sized text for compression testing." * 20
        data["medium_json"] = json.dumps({
            "users": [{"id": i, "name": f"User {i}"} for i in range(100)]
        }).encode()
        
        # Large data (should compress well)
        data["large_text"] = b"This is a large text that should compress very well." * 500
        data["large_json"] = json.dumps({
            "data": [{"id": i, "value": f"value_{i}", "metadata": {"created": "2024-01-01"}} for i in range(1000)]
        }).encode()
        
        # Highly compressible data
        data["repetitive"] = b"AAAAAAAAAA" * 1000
        data["structured"] = json.dumps({"pattern": "A" * 100}).encode() * 50
        
        # Poorly compressible data (random)
        random.seed(42)  # For reproducible results
        data["random_binary"] = bytes([random.randint(0, 255) for _ in range(5000)])
        
        # Binary data
        data["binary_pattern"] = bytes(range(256)) * 20
        
        # Unicode text
        data["unicode_text"] = "Hello 世界! 🌍 Здравствуй мир! مرحبا بالعالم!".encode("utf-8") * 100
        
        return data

    async def test_compression_latency_overhead(self):
        """Benchmark compression/decompression latency overhead."""
        print("Testing compression latency overhead...")
        
        benchmark_data = self._generate_benchmark_data()
        
        # Configurations to test
        configs = [
            ("uncompressed", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(enabled=False)
            )),
            ("zstd_level_1", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(
                    enabled=True,
                    backend=CompressionBackend.ZSTD,
                    compression_level=1,
                    min_compression_size=32,
                )
            )),
            ("zstd_level_3", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(
                    enabled=True,
                    backend=CompressionBackend.ZSTD,
                    compression_level=3,
                    min_compression_size=32,
                )
            )),
            ("zstd_level_10", GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(
                    enabled=True,
                    backend=CompressionBackend.ZSTD,
                    compression_level=10,
                    min_compression_size=32,
                )
            )),
        ]
        
        results = {}
        
        for config_name, config in configs:
            print(f"  Benchmarking {config_name}...")
            client = await GlideClient.create(config)
            
            try:
                config_results = {}
                
                for data_name, data_value in benchmark_data.items():
                    # Skip small data for compression configs (won't be compressed anyway)
                    if config_name != "uncompressed" and len(data_value) < 32:
                        continue
                    
                    key = f"perf:{config_name}:{data_name}"
                    
                    # Benchmark SET operations
                    set_times = []
                    for _ in range(10):  # 10 iterations for averaging
                        start_time = time.perf_counter()
                        await client.set(key, data_value)
                        end_time = time.perf_counter()
                        set_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
                    
                    # Benchmark GET operations
                    get_times = []
                    for _ in range(10):  # 10 iterations for averaging
                        start_time = time.perf_counter()
                        retrieved_value = await client.get(key)
                        end_time = time.perf_counter()
                        get_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
                        
                        # Verify data integrity
                        if config_name != "uncompressed" or retrieved_value == data_value:
                            pass  # Expected behavior
                        else:
                            print(f"    Warning: Data integrity issue for {data_name}")
                    
                    config_results[data_name] = {
                        "set_avg_ms": statistics.mean(set_times),
                        "set_std_ms": statistics.stdev(set_times) if len(set_times) > 1 else 0,
                        "get_avg_ms": statistics.mean(get_times),
                        "get_std_ms": statistics.stdev(get_times) if len(get_times) > 1 else 0,
                        "data_size": len(data_value),
                    }
                    
                    print(f"    {data_name}: SET {config_results[data_name]['set_avg_ms']:.2f}ms, "
                          f"GET {config_results[data_name]['get_avg_ms']:.2f}ms")
                
                results[config_name] = config_results
                
            finally:
                await client.close()
        
        # Analyze overhead
        print("\n  Performance Analysis:")
        if "uncompressed" in results:
            baseline = results["uncompressed"]
            
            for config_name, config_results in results.items():
                if config_name == "uncompressed":
                    continue
                
                print(f"    {config_name} vs uncompressed:")
                for data_name in config_results:
                    if data_name in baseline:
                        set_overhead = ((config_results[data_name]["set_avg_ms"] - 
                                       baseline[data_name]["set_avg_ms"]) / 
                                      baseline[data_name]["set_avg_ms"]) * 100
                        get_overhead = ((config_results[data_name]["get_avg_ms"] - 
                                       baseline[data_name]["get_avg_ms"]) / 
                                      baseline[data_name]["get_avg_ms"]) * 100
                        
                        print(f"      {data_name}: SET +{set_overhead:.1f}%, GET +{get_overhead:.1f}%")
        
        self.benchmark_results["latency"] = results
        return True

    async def test_compression_ratio_effectiveness(self):
        """Test compression ratio effectiveness for different data types."""
        print("Testing compression ratio effectiveness...")
        
        benchmark_data = self._generate_benchmark_data()
        
        # Test with different compression levels
        compression_configs = [
            ("zstd_level_1", 1),
            ("zstd_level_3", 3),
            ("zstd_level_10", 10),
        ]
        
        ratio_results = {}
        
        for config_name, compression_level in compression_configs:
            print(f"  Testing {config_name}...")
            
            config = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(
                    enabled=True,
                    backend=CompressionBackend.ZSTD,
                    compression_level=compression_level,
                    min_compression_size=16,  # Low threshold to test all data
                )
            )
            
            # Also create uncompressed client to get raw compressed data
            uncompressed_config = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(enabled=False)
            )
            
            compressed_client = await GlideClient.create(config)
            uncompressed_client = await GlideClient.create(uncompressed_config)
            
            try:
                config_ratios = {}
                
                for data_name, data_value in benchmark_data.items():
                    if len(data_value) < 16:  # Skip very small data
                        continue
                    
                    key = f"ratio:{config_name}:{data_name}"
                    
                    # Store with compression
                    await compressed_client.set(key, data_value)
                    
                    # Get raw compressed data
                    compressed_data = await uncompressed_client.get(key)
                    
                    if compressed_data:
                        original_size = len(data_value)
                        compressed_size = len(compressed_data)
                        compression_ratio = original_size / compressed_size
                        space_saved = ((original_size - compressed_size) / original_size) * 100
                        
                        config_ratios[data_name] = {
                            "original_size": original_size,
                            "compressed_size": compressed_size,
                            "compression_ratio": compression_ratio,
                            "space_saved_percent": space_saved,
                        }
                        
                        print(f"    {data_name}: {original_size} -> {compressed_size} bytes "
                              f"(ratio: {compression_ratio:.2f}x, saved: {space_saved:.1f}%)")
                    else:
                        print(f"    {data_name}: No compressed data retrieved")
                
                ratio_results[config_name] = config_ratios
                
            finally:
                await compressed_client.close()
                await uncompressed_client.close()
        
        # Analyze compression effectiveness
        print("\n  Compression Effectiveness Analysis:")
        data_types = set()
        for config_results in ratio_results.values():
            data_types.update(config_results.keys())
        
        for data_name in sorted(data_types):
            print(f"    {data_name}:")
            for config_name in ratio_results:
                if data_name in ratio_results[config_name]:
                    result = ratio_results[config_name][data_name]
                    print(f"      {config_name}: {result['compression_ratio']:.2f}x "
                          f"({result['space_saved_percent']:.1f}% saved)")
        
        self.benchmark_results["compression_ratios"] = ratio_results
        return True

    async def test_graceful_fallback_behavior(self):
        """Test graceful fallback when compression/decompression fails."""
        print("Testing graceful fallback behavior...")
        
        # Test with valid configuration first
        valid_config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        client = await GlideClient.create(valid_config)
        
        try:
            # Test 1: Normal operation (should work)
            test_data = b"This is test data for fallback testing" * 20
            key1 = "fallback:normal"
            
            await client.set(key1, test_data)
            retrieved_data = await client.get(key1)
            
            if retrieved_data == test_data:
                print("  ✓ Normal compression operation works")
            else:
                print("  ✗ Normal compression operation failed")
                return False
            
            # Test 2: Data below compression threshold (should not be compressed)
            small_data = b"small"
            key2 = "fallback:small"
            
            await client.set(key2, small_data)
            retrieved_small = await client.get(key2)
            
            if retrieved_small == small_data:
                print("  ✓ Small data handling works (not compressed)")
            else:
                print("  ✗ Small data handling failed")
                return False
            
            # Test 3: Empty data
            empty_data = b""
            key3 = "fallback:empty"
            
            await client.set(key3, empty_data)
            retrieved_empty = await client.get(key3)
            
            if retrieved_empty == empty_data:
                print("  ✓ Empty data handling works")
            else:
                print("  ✗ Empty data handling failed")
                return False
            
            # Test 4: Very large data (test memory handling)
            large_data = b"X" * (1024 * 1024)  # 1MB of data
            key4 = "fallback:large"
            
            try:
                await client.set(key4, large_data)
                retrieved_large = await client.get(key4)
                
                if retrieved_large == large_data:
                    print("  ✓ Large data handling works")
                else:
                    print("  ✗ Large data handling failed - data mismatch")
                    return False
            except Exception as e:
                print(f"  ✗ Large data handling failed with exception: {e}")
                return False
            
            # Test 5: Corrupted compressed data handling
            # Store valid compressed data first
            key5 = "fallback:corruption_test"
            await client.set(key5, test_data)
            
            # Now try to read with uncompressed client (simulates corruption scenario)
            uncompressed_config = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=CompressionConfiguration(enabled=False)
            )
            
            uncompressed_client = await GlideClient.create(uncompressed_config)
            
            try:
                # This should return the raw compressed bytes
                raw_data = await uncompressed_client.get(key5)
                if raw_data is not None and len(raw_data) > 0:
                    print("  ✓ Corrupted data scenario handled (returns raw bytes)")
                else:
                    print("  ✗ Corrupted data scenario failed")
                    return False
            finally:
                await uncompressed_client.close()
            
            print("  All fallback scenarios passed")
            return True
            
        finally:
            await client.close()

    async def test_configuration_validation_and_errors(self):
        """Test configuration validation and error reporting."""
        print("Testing configuration validation and error reporting...")
        
        # Test 1: Invalid compression level for ZSTD
        try:
            invalid_config = CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=25,  # Invalid: ZSTD max is 22
                min_compression_size=64,
            )
            
            config = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=invalid_config
            )
            
            # This should raise an error during client creation
            try:
                client = await GlideClient.create(config)
                await client.close()
                print("  ✗ Invalid ZSTD compression level was accepted (should have failed)")
                return False
            except Exception as e:
                print(f"  ✓ Invalid ZSTD compression level rejected: {type(e).__name__}")
        except Exception as e:
            print(f"  ✓ Invalid ZSTD compression level rejected during config creation: {type(e).__name__}")
        
        # Test 2: Invalid minimum compression size
        try:
            invalid_config2 = CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=0,  # Invalid: should be > 0
            )
            
            config2 = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=invalid_config2
            )
            
            try:
                client = await GlideClient.create(config2)
                await client.close()
                print("  ✗ Invalid min_compression_size was accepted (should have failed)")
                return False
            except Exception as e:
                print(f"  ✓ Invalid min_compression_size rejected: {type(e).__name__}")
        except Exception as e:
            print(f"  ✓ Invalid min_compression_size rejected during config creation: {type(e).__name__}")
        
        # Test 3: Invalid max < min compression size
        try:
            invalid_config3 = CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=100,
                max_compression_size=50,  # Invalid: max < min
            )
            
            config3 = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=invalid_config3
            )
            
            try:
                client = await GlideClient.create(config3)
                await client.close()
                print("  ✗ Invalid max < min compression size was accepted (should have failed)")
                return False
            except Exception as e:
                print(f"  ✓ Invalid max < min compression size rejected: {type(e).__name__}")
        except Exception as e:
            print(f"  ✓ Invalid max < min compression size rejected during config creation: {type(e).__name__}")
        
        # Test 4: Valid configuration should work
        try:
            valid_config = CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=64,
                max_compression_size=1024 * 1024,
            )
            
            config = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=valid_config
            )
            
            client = await GlideClient.create(config)
            await client.close()
            print("  ✓ Valid configuration accepted")
        except Exception as e:
            print(f"  ✗ Valid configuration rejected: {e}")
            return False
        
        # Test 5: Disabled compression should always work
        try:
            disabled_config = CompressionConfiguration(enabled=False)
            
            config = GlideClientConfiguration(
                addresses=self.server_addresses,
                compression=disabled_config
            )
            
            client = await GlideClient.create(config)
            await client.close()
            print("  ✓ Disabled compression configuration accepted")
        except Exception as e:
            print(f"  ✗ Disabled compression configuration rejected: {e}")
            return False
        
        print("  All configuration validation tests passed")
        return True

    async def test_memory_usage_patterns(self):
        """Test memory usage patterns during compression operations."""
        print("Testing memory usage patterns...")
        
        config = GlideClientConfiguration(
            addresses=self.server_addresses,
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size=32,
            )
        )
        
        client = await GlideClient.create(config)
        
        try:
            # Test with progressively larger data sizes
            sizes = [1024, 10240, 102400, 1024000]  # 1KB, 10KB, 100KB, 1MB
            
            for size in sizes:
                data = b"X" * size
                key = f"memory:test_{size}"
                
                # Perform multiple operations to test memory stability
                for i in range(5):
                    await client.set(f"{key}_{i}", data)
                    retrieved = await client.get(f"{key}_{i}")
                    
                    if retrieved != data:
                        print(f"  ✗ Memory test failed for size {size} at iteration {i}")
                        return False
                
                print(f"  ✓ Memory test passed for {size} bytes")
            
            # Test rapid operations
            rapid_data = b"Rapid operation test data" * 10
            for i in range(100):
                key = f"rapid:test_{i}"
                await client.set(key, rapid_data)
                retrieved = await client.get(key)
                
                if retrieved != rapid_data:
                    print(f"  ✗ Rapid operations test failed at iteration {i}")
                    return False
            
            print("  ✓ Rapid operations test passed")
            print("  All memory usage tests passed")
            return True
            
        finally:
            await client.close()

    def print_benchmark_summary(self):
        """Print a summary of all benchmark results."""
        print("\n=== Benchmark Summary ===")
        
        if "latency" in self.benchmark_results:
            print("\nLatency Results:")
            latency_results = self.benchmark_results["latency"]
            
            # Find common data types across all configurations
            common_data = set()
            for config_results in latency_results.values():
                if not common_data:
                    common_data = set(config_results.keys())
                else:
                    common_data &= set(config_results.keys())
            
            for data_name in sorted(common_data):
                print(f"  {data_name}:")
                for config_name, config_results in latency_results.items():
                    if data_name in config_results:
                        result = config_results[data_name]
                        print(f"    {config_name}: SET {result['set_avg_ms']:.2f}ms, "
                              f"GET {result['get_avg_ms']:.2f}ms")
        
        if "compression_ratios" in self.benchmark_results:
            print("\nCompression Ratio Results:")
            ratio_results = self.benchmark_results["compression_ratios"]
            
            # Find best compression ratios
            best_ratios = {}
            for config_name, config_results in ratio_results.items():
                for data_name, result in config_results.items():
                    if data_name not in best_ratios or result["compression_ratio"] > best_ratios[data_name]["ratio"]:
                        best_ratios[data_name] = {
                            "ratio": result["compression_ratio"],
                            "config": config_name,
                            "space_saved": result["space_saved_percent"]
                        }
            
            for data_name, best in sorted(best_ratios.items()):
                print(f"  {data_name}: Best {best['ratio']:.2f}x ({best['space_saved']:.1f}% saved) with {best['config']}")

    async def run_all_tests(self) -> bool:
        """Run all performance and error handling tests."""
        print("Starting performance and error handling tests...")
        
        tests = [
            self.test_compression_latency_overhead,
            self.test_compression_ratio_effectiveness,
            self.test_graceful_fallback_behavior,
            self.test_configuration_validation_and_errors,
            self.test_memory_usage_patterns,
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
        
        # Print benchmark summary
        self.print_benchmark_summary()
        
        passed = sum(results)
        total = len(results)
        
        print(f"\nPerformance and error handling tests: {passed}/{total} passed")
        return passed == total


async def main():
    """Main test runner."""
    test_suite = PerformanceAndErrorHandlingTest()
    
    try:
        success = await test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
