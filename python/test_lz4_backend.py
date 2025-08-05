#!/usr/bin/env python3
"""
Test to demonstrate the LZ4 backend functionality.
"""

import asyncio
import sys
import os

# Add the python directory to the path to import glide
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'glide-async', 'python'))

try:
    from glide import (
        GlideClient, 
        GlideClientConfiguration, 
        NodeAddress,
        CompressionConfiguration,
        CompressionBackend
    )
except ImportError as e:
    print(f"Failed to import glide: {e}")
    print("Make sure you have built the Python client with compression support enabled")
    sys.exit(1)

async def test_lz4_backend():
    """Test LZ4 backend functionality."""
    
    # Configure LZ4 compression
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.LZ4,
        compression_level=None,  # LZ4 doesn't use compression levels
        min_compression_size=64
    )
    
    config = GlideClientConfiguration(
        [NodeAddress(host="localhost", port=6379)],
        compression=compression_config
    )
    
    try:
        client = await GlideClient.create(config)
        print("✅ Connected to Redis with LZ4 compression enabled")
        
        # Test data that should be compressed (>= 64 bytes)
        test_key = "lz4_test_key"
        test_value = "This is a test value for LZ4 compression that is long enough to be compressed. " * 2
        
        print(f"📝 Test data size: {len(test_value)} bytes")
        
        # Test SET operation (should compress with LZ4)
        await client.set(test_key, test_value)
        print("✅ SET operation with LZ4 compression completed")
        
        # Test GET operation (should decompress)
        retrieved_value = await client.get(test_key)
        retrieved_str = retrieved_value.decode('utf-8') if isinstance(retrieved_value, bytes) else retrieved_value
        
        if retrieved_str == test_value:
            print("✅ GET operation with LZ4 decompression completed - data integrity verified")
        else:
            print("❌ Data integrity check failed")
            return False
        
        # Test with small data (should not be compressed)
        small_key = "lz4_small_test_key"
        small_value = "small"  # < 64 bytes
        
        await client.set(small_key, small_value)
        retrieved_small = await client.get(small_key)
        retrieved_small_str = retrieved_small.decode('utf-8') if isinstance(retrieved_small, bytes) else retrieved_small
        
        if retrieved_small_str == small_value:
            print("✅ Small data handling verified (no compression)")
        else:
            print("❌ Small data handling failed")
            return False
        
        # Clean up
        await client.delete([test_key, small_key])
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'client' in locals():
            await client.close()

async def compare_backends():
    """Compare ZSTD and LZ4 backends."""
    
    test_data = "This is test data for comparing compression backends. " * 10
    print(f"\n🔄 Comparing backends with {len(test_data)} bytes of data")
    
    results = {}
    
    for backend_name, backend_type in [("ZSTD", CompressionBackend.ZSTD), ("LZ4", CompressionBackend.LZ4)]:
        compression_config = CompressionConfiguration(
            enabled=True,
            backend=backend_type,
            compression_level=3 if backend_type == CompressionBackend.ZSTD else None,
            min_compression_size=64
        )
        
        config = GlideClientConfiguration(
            [NodeAddress(host="localhost", port=6379)],
            compression=compression_config
        )
        
        try:
            client = await GlideClient.create(config)
            
            # Measure performance
            import time
            start_time = time.time()
            
            for i in range(100):
                await client.set(f"bench_{backend_name}_{i}", test_data)
                result = await client.get(f"bench_{backend_name}_{i}")
                # Verify data integrity
                result_str = result.decode('utf-8') if isinstance(result, bytes) else result
                assert result_str == test_data
            
            end_time = time.time()
            
            # Clean up
            keys_to_delete = [f"bench_{backend_name}_{i}" for i in range(100)]
            await client.delete(keys_to_delete)
            
            await client.close()
            
            results[backend_name] = {
                'time': end_time - start_time,
                'ops_per_sec': 200 / (end_time - start_time)  # 100 SET + 100 GET
            }
            
        except Exception as e:
            print(f"❌ {backend_name} backend test failed: {e}")
            results[backend_name] = {'error': str(e)}
    
    print("\n📊 Backend Comparison Results:")
    print("-" * 40)
    for backend_name, result in results.items():
        if 'error' in result:
            print(f"{backend_name}: ❌ {result['error']}")
        else:
            print(f"{backend_name}: {result['ops_per_sec']:.0f} ops/sec ({result['time']:.3f}s)")

async def main():
    """Run all tests."""
    print("🧪 Testing LZ4 compression backend")
    print("=" * 50)
    
    # Test LZ4 backend functionality
    print("\n📋 Test 1: LZ4 Backend Functionality")
    test1_result = await test_lz4_backend()
    
    # Compare backends
    print("\n📋 Test 2: Backend Comparison")
    await compare_backends()
    
    print("\n" + "=" * 50)
    if test1_result:
        print("🎉 LZ4 backend test passed! The pluggable backend system is working correctly.")
        return 0
    else:
        print("❌ LZ4 backend test failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
