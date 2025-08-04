#!/usr/bin/env python3
# Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

"""
Interactive Compression Session

This script sets up an interactive Python session with a compression-enabled
GLIDE client wrapper that handles async calls for you, so you can use it
synchronously in an interactive session.
"""

import asyncio
import sys
import os

# Add the python directory to the path to import glide
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python', 'python'))

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  redis package not found. Memory usage commands will be limited.")
    print("   Install with: pip install redis")

from glide import (
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    CompressionConfiguration,
    CompressionBackend,
)

class SyncGlideWrapper:
    """Synchronous wrapper around async GLIDE client for interactive use"""
    
    def __init__(self, async_client, loop):
        self._client = async_client
        self._loop = loop
    
    def _run_async(self, coro):
        """Helper to run async coroutines synchronously"""
        try:
            return self._loop.run_until_complete(coro)
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                # Create a new loop if the current one is closed
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                return self._loop.run_until_complete(coro)
            raise
    
    def set(self, key, value):
        """Set a key-value pair (synchronous)"""
        return self._run_async(self._client.set(key, value))
    
    def get(self, key):
        """Get a value by key (synchronous)"""
        result = self._run_async(self._client.get(key))
        # Convert bytes to string for easier interactive use
        if isinstance(result, bytes):
            return result.decode('utf-8')
        return result
    
    def get_raw(self, key):
        """Get raw bytes value by key (synchronous)"""
        return self._run_async(self._client.get(key))
    
    def delete(self, *keys):
        """Delete one or more keys (synchronous)"""
        return self._run_async(self._client.delete(keys))
    
    def exists(self, *keys):
        """Check if keys exist (synchronous)"""
        return self._run_async(self._client.exists(keys))
    
    def mset(self, key_value_map):
        """Set multiple key-value pairs (synchronous)"""
        return self._run_async(self._client.mset(key_value_map))
    
    def mget(self, keys):
        """Get multiple values by keys (synchronous)"""
        results = self._run_async(self._client.mget(keys))
        # Convert bytes to strings for easier interactive use
        return [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]
    
    def mget_raw(self, keys):
        """Get multiple raw bytes values by keys (synchronous)"""
        return self._run_async(self._client.mget(keys))
    
    def keys(self, pattern="*"):
        """Get keys matching pattern (synchronous)"""
        return self._run_async(self._client.keys(pattern))
    
    def info(self, *sections):
        """Get server info (synchronous)"""
        return self._run_async(self._client.info(sections))
    
    def memory_usage(self, key):
        """Get memory usage for a key using GLIDE's custom command"""
        try:
            result = self._run_async(self._client.custom_command(["MEMORY", "USAGE", key]))
            return int(result) if result is not None else 0
        except Exception as e:
            print(f"⚠️  Could not get memory usage: {e}")
            return 0
    
    def close(self):
        """Close the client (synchronous)"""
        self._run_async(self._client.close())
        if not self._loop.is_closed():
            self._loop.close()

def setup_session():
    """Set up the interactive session with sync wrapper"""
    print("🚀 Setting up Interactive Compression Session")
    print("=" * 50)
    
    # Create compression configuration
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
    
    # Create the async client and wrap it
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async_client = loop.run_until_complete(GlideClient.create(config))
    client = SyncGlideWrapper(async_client, loop)
    
    # Create a direct Redis client for memory measurements if available
    redis_client = None
    if REDIS_AVAILABLE:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=False)
        print("✅ Direct Redis client created for memory measurements!")
    
    print("✅ Compression-enabled GLIDE client created!")
    print()
    print("📋 Available objects:")
    print("   • client - Sync GLIDE wrapper with ZSTD compression (level 3, min 64 bytes)")
    if REDIS_AVAILABLE:
        print("   • redis_client - Direct Redis client for MEMORY USAGE commands")
    else:
        print("   • client.memory_usage(key) - Memory usage via GLIDE (limited functionality)")
    print()
    print("🔧 Compression Configuration:")
    print("   • Backend: ZSTD")
    print("   • Level: 3")
    print("   • Min compression size: 64 bytes")
    print("   • Data <64 bytes will NOT be compressed")
    print()
    print("💡 Example commands to try:")
    print("   # Set some data")
    print("   client.set('test_key', 'your_data_here')")
    print()
    print("   # Get the data back")
    print("   result = client.get('test_key')")
    print("   print(f'Retrieved: {result}')")
    print()
    print("   # Check memory usage in Redis")
    if REDIS_AVAILABLE:
        print("   memory_usage = redis_client.memory_usage('test_key')")
    else:
        print("   memory_usage = client.memory_usage('test_key')")
    print("   print(f'Memory usage: {memory_usage} bytes')")
    print()
    print("   # Quick compression test")
    print("   quick_test('some data to compress')")
    print()
    print("   # Compare compression ratios")
    print("   compare_compression('larger data that should compress well' * 10)")
    print()
    print("🎯 Ready for interactive testing!")
    print("=" * 50)
    
    return client, redis_client, loop

def quick_test(data, key_suffix=""):
    """Quick test function to set data and check compression"""
    key = f"test{key_suffix}"
    client.set(key, data)
    result = client.get(key)
    
    if redis_client:
        memory = redis_client.memory_usage(key)
    else:
        memory = client.memory_usage(key)
    
    print(f"Data: {len(data)} bytes")
    print(f"Retrieved: {len(result)} bytes")
    print(f"Memory in Redis: {memory} bytes")
    print(f"Data matches: {result == data}")
    return result, memory

def compare_compression(data, key_base="compare"):
    """Compare compressed vs uncompressed storage"""
    # Compressed
    client.set(f"{key_base}_compressed", data)
    if redis_client:
        compressed_memory = redis_client.memory_usage(f"{key_base}_compressed")
    else:
        compressed_memory = client.memory_usage(f"{key_base}_compressed")
    
    # Uncompressed - create a new client without compression
    config_no_compression = GlideClientConfiguration([NodeAddress(host="localhost", port=6379)])
    temp_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(temp_loop)
    async_client_no_compression = temp_loop.run_until_complete(GlideClient.create(config_no_compression))
    client_no_compression = SyncGlideWrapper(async_client_no_compression, temp_loop)
    
    client_no_compression.set(f"{key_base}_uncompressed", data)
    if redis_client:
        uncompressed_memory = redis_client.memory_usage(f"{key_base}_uncompressed")
    else:
        uncompressed_memory = client_no_compression.memory_usage(f"{key_base}_uncompressed")
    client_no_compression.close()
    
    ratio = uncompressed_memory / compressed_memory if compressed_memory > 0 else 0
    savings = uncompressed_memory - compressed_memory
    savings_percent = (savings / uncompressed_memory * 100) if uncompressed_memory > 0 else 0
    
    print(f"Original data: {len(data)} bytes")
    print(f"Uncompressed in Redis: {uncompressed_memory} bytes")
    print(f"Compressed in Redis: {compressed_memory} bytes")
    print(f"Compression ratio: {ratio:.2f}:1")
    print(f"Space saved: {savings} bytes ({savings_percent:.1f}%)")
    
    return compressed_memory, uncompressed_memory, ratio

def create_client_with_level(level):
    """Create a new client with a specific compression level"""
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
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async_client = loop.run_until_complete(GlideClient.create(config))
    return SyncGlideWrapper(async_client, loop)

# Set up the session
print("Starting interactive session...")
client, redis_client, loop = setup_session()

# Start an interactive session
import code

# Create a custom console with the clients available
console_locals = {
    'client': client,
    'redis_client': redis_client,
    'quick_test': quick_test,
    'compare_compression': compare_compression,
    'create_client_with_level': create_client_with_level,
    'CompressionBackend': CompressionBackend,
    'GlideClientConfiguration': GlideClientConfiguration,
    'NodeAddress': NodeAddress,
    'CompressionConfiguration': CompressionConfiguration,
}

print("\n🎮 Interactive session ready!")
print()
print("🔧 Available functions:")
print("   • client.set(key, value) - Set a key-value pair")
print("   • client.get(key) - Get a value (auto-converts bytes to string)")
print("   • client.get_raw(key) - Get raw bytes value")
print("   • client.delete(key1, key2, ...) - Delete keys")
print("   • client.mset({key1: val1, key2: val2}) - Set multiple")
print("   • client.mget([key1, key2]) - Get multiple")
print("   • client.memory_usage(key) or redis_client.memory_usage(key) - Check Redis memory usage")
print("   • quick_test('data') - Quick compression test")
print("   • compare_compression('data') - Compare compressed vs uncompressed")
print("   • create_client_with_level(6) - Create client with specific compression level")
print()
print("Type your commands below. Use Ctrl+C to exit.")
print()

try:
    code.interact(local=console_locals, banner="")
except KeyboardInterrupt:
    print("\n👋 Closing session...")
finally:
    # Clean up
    client.close()
    if redis_client:
        redis_client.close()
    print("✅ Session closed!")
