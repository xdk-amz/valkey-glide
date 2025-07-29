#!/usr/bin/env python3
# Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

"""
Simple Compression Demo

This script demonstrates that compression is working in Valkey GLIDE Python client.
"""

import asyncio
from glide import (
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    CompressionConfiguration,
    CompressionBackend,
)


async def simple_demo():
    print("🚀 Simple Valkey GLIDE Compression Demo")
    print("=" * 45)
    
    # Test data
    test_data = "Hello, World! This is a test of compression. " * 50
    print(f"📊 Test data size: {len(test_data)} bytes")
    print()
    
    # Configuration with compression
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=3,
        min_compression_size=64
    )
    
    config = GlideClientConfiguration(
        [NodeAddress(host="localhost", port=6379)],
        compression=compression_config
    )
    
    print("🗜️  Creating client with ZSTD compression (level 3)...")
    client = await GlideClient.create(config)
    
    # Test basic operations
    print("📝 Setting compressed data...")
    await client.set("compression_test", test_data)
    
    print("📖 Getting compressed data...")
    result = await client.get("compression_test")
    
    print(f"✅ Retrieved data size: {len(result) if result else 0} bytes")
    print(f"🔍 Data matches: {result == test_data}")
    
    if result == test_data:
        print("🎉 Compression is working correctly!")
    else:
        print("⚠️  Data mismatch - investigating...")
        print(f"   Original: {test_data[:100]}...")
        print(f"   Retrieved: {result[:100] if result else 'None'}...")
    
    await client.close()
    print("✨ Demo completed!")


if __name__ == "__main__":
    asyncio.run(simple_demo())
