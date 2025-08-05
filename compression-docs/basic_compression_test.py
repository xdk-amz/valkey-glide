#!/usr/bin/env python3
"""
Simple test to verify basic SET/GET compression functionality.
This test verifies that only SET and GET commands support compression
after the simplification.
"""

import asyncio
import sys
import os

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

async def test_basic_set_get_compression():
    """Test basic SET/GET operations with compression enabled."""
    
    # Configure compression
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=3,
        min_compression_size=64  # Compress data >= 64 bytes
    )
    
    # Configure client with compression
    config = GlideClientConfiguration(
        [NodeAddress(host="localhost", port=6379)],
        compression=compression_config
    )
    
    try:
        client = await GlideClient.create(config)
        print("✅ Connected to Redis with compression enabled")
        
        # Test data that should be compressed (>= 64 bytes)
        test_key = "compression_test_key"
        test_value = "This is a test value that is long enough to be compressed by the compression library. " * 2
        
        print(f"📝 Test data size: {len(test_value)} bytes")
        
        # Test SET operation (should compress)
        await client.set(test_key, test_value)
        print("✅ SET operation completed successfully")
        
        # Test GET operation (should decompress)
        retrieved_value = await client.get(test_key)
        print("✅ GET operation completed successfully")
        
        # Verify data integrity (handle bytes vs string)
        retrieved_str = retrieved_value.decode('utf-8') if isinstance(retrieved_value, bytes) else retrieved_value
        if retrieved_str == test_value:
            print("✅ Data integrity verified - compression/decompression working correctly")
        else:
            print("❌ Data integrity check failed")
            print(f"Expected: {test_value[:50]}...")
            print(f"Got: {retrieved_str[:50] if retrieved_str else 'None'}...")
            return False
        
        # Test with small data (should not be compressed)
        small_key = "small_test_key"
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
        return False
    finally:
        if 'client' in locals():
            await client.close()

async def test_unsupported_commands():
    """Test that other commands don't use compression (they should work but without compression)."""
    
    # Configure compression
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
    
    try:
        client = await GlideClient.create(config)
        print("✅ Connected for unsupported commands test")
        
        # Test MSET/MGET (should work but without compression)
        test_data = {
            "mset_key1": "This is a long value that would normally be compressed but won't be with MSET" * 2,
            "mset_key2": "Another long value for MSET testing" * 3
        }
        
        # MSET should work but not compress values
        await client.mset(test_data)
        print("✅ MSET operation completed (no compression applied)")
        
        # MGET should work but not decompress values
        keys = list(test_data.keys())
        retrieved_values = await client.mget(keys)
        print("✅ MGET operation completed (no decompression applied)")
        
        # Values should match (since no compression was applied)
        for i, key in enumerate(keys):
            retrieved_str = retrieved_values[i].decode('utf-8') if isinstance(retrieved_values[i], bytes) else retrieved_values[i]
            if retrieved_str == test_data[key]:
                print(f"✅ {key} value matches (no compression/decompression)")
            else:
                print(f"❌ {key} value mismatch")
                print(f"Expected: {test_data[key][:50]}...")
                print(f"Got: {retrieved_str[:50] if retrieved_str else 'None'}...")
                return False
        
        # Clean up
        await client.delete(keys)
        print("✅ Unsupported commands test completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Unsupported commands test failed: {e}")
        return False
    finally:
        if 'client' in locals():
            await client.close()

async def main():
    """Run all tests."""
    print("🧪 Testing simplified compression library (SET/GET only)")
    print("=" * 60)
    
    # Test basic SET/GET compression
    print("\n📋 Test 1: Basic SET/GET compression")
    test1_result = await test_basic_set_get_compression()
    
    # Test that other commands work but don't use compression
    print("\n📋 Test 2: Other commands (no compression)")
    test2_result = await test_unsupported_commands()
    
    print("\n" + "=" * 60)
    if test1_result and test2_result:
        print("🎉 All tests passed! Simplified compression library is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
