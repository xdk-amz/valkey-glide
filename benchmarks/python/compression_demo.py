#!/usr/bin/env python3
# Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

"""
Compression Feature Demo

This script demonstrates the compression feature in Valkey GLIDE Python client,
showing configuration options, performance comparison, and validation.
"""

import asyncio
import time
from glide import (
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    CompressionConfiguration,
    CompressionBackend,
)


async def demonstrate_compression():
    print("🚀 Valkey GLIDE Compression Demo")
    print("=" * 50)
    
    # Test data - highly compressible
    test_data = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50
    print(f"📊 Test data size: {len(test_data)} bytes")
    print(f"📝 Sample data: {test_data[:100]}...")
    print()
    
    # Configuration without compression
    config_no_compression = GlideClientConfiguration(
        [NodeAddress(host="localhost", port=6379)]
    )
    
    # Configuration with compression
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=3,
        min_compression_size=64
    )
    
    config_with_compression = GlideClientConfiguration(
        [NodeAddress(host="localhost", port=6379)],
        compression=compression_config
    )
    
    # Test without compression
    print("🔄 Testing WITHOUT compression...")
    client_no_compression = await GlideClient.create(config_no_compression)
    
    start_time = time.perf_counter()
    for i in range(100):
        await client_no_compression.set(f"test:no_compression:{i}", test_data)
    
    for i in range(100):
        result = await client_no_compression.get(f"test:no_compression:{i}")
        # Convert bytes to string for comparison
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert result == test_data, f"Data mismatch at key {i}"
    
    no_compression_time = time.perf_counter() - start_time
    await client_no_compression.close()
    
    print(f"   ✅ Completed 200 operations in {no_compression_time:.3f} seconds")
    print(f"   📈 Rate: {200/no_compression_time:.0f} ops/sec")
    print()
    
    # Test with compression
    print("🗜️  Testing WITH compression (ZSTD level 3)...")
    client_with_compression = await GlideClient.create(config_with_compression)
    
    start_time = time.perf_counter()
    for i in range(100):
        await client_with_compression.set(f"test:with_compression:{i}", test_data)
    
    for i in range(100):
        result = await client_with_compression.get(f"test:with_compression:{i}")
        # Convert bytes to string for comparison
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert result == test_data, f"Data mismatch at key {i}"
    
    compression_time = time.perf_counter() - start_time
    await client_with_compression.close()
    
    print(f"   ✅ Completed 200 operations in {compression_time:.3f} seconds")
    print(f"   📈 Rate: {200/compression_time:.0f} ops/sec")
    print()
    
    # Compare results
    print("📊 Performance Comparison:")
    print("-" * 30)
    if compression_time < no_compression_time:
        improvement = ((no_compression_time - compression_time) / no_compression_time) * 100
        print(f"   🎉 Compression is {improvement:.1f}% FASTER!")
    else:
        overhead = ((compression_time - no_compression_time) / no_compression_time) * 100
        print(f"   ⚠️  Compression has {overhead:.1f}% overhead")
    
    print(f"   📉 Time difference: {abs(compression_time - no_compression_time):.3f} seconds")
    print()
    
    # Demonstrate different compression levels
    print("🔧 Testing different compression levels...")
    print("-" * 40)
    
    for level in [1, 3, 6]:
        compression_config = CompressionConfiguration(
            enabled=True,
            backend=CompressionBackend.ZSTD,
            compression_level=level,
            min_compression_size=64
        )
        
        config = GlideClientConfiguration(
            [NodeAddress(host="localhost", port=6379)],
            compression=compression_config
        )
        
        client = await GlideClient.create(config)
        
        start_time = time.perf_counter()
        for i in range(50):
            await client.set(f"test:level_{level}:{i}", test_data)
            result = await client.get(f"test:level_{level}:{i}")
            # Convert bytes to string for comparison
            if isinstance(result, bytes):
                result = result.decode('utf-8')
            assert result == test_data, f"Data mismatch at level {level}, key {i}"
        
        level_time = time.perf_counter() - start_time
        await client.close()
        
        print(f"   Level {level}: {100/level_time:.0f} ops/sec ({level_time:.3f}s for 100 ops)")
    
    print()
    print("✨ Demo completed successfully!")
    print("💡 Key takeaways:")
    print("   • Compression can improve performance for large, compressible data")
    print("   • Lower compression levels (1) are faster but compress less")
    print("   • Higher compression levels (6) compress more but are slower")
    print("   • Optimal level depends on your data and performance requirements")
    print("   • Data integrity is maintained through compression/decompression cycle")


if __name__ == "__main__":
    asyncio.run(demonstrate_compression())
