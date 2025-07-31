#!/usr/bin/env python3
"""
Simple Compression Test Session

A simplified interactive session for testing Redis compression
using just the redis-py library.
"""

import redis
import json
import time

def setup_redis_clients():
    """Set up Redis clients for testing"""
    print("🚀 Setting up Simple Compression Test Session")
    print("=" * 50)
    
    # Create Redis client
    client = redis.Redis(host='localhost', port=6379, decode_responses=False)
    
    # Test connection
    try:
        client.ping()
        print("✅ Connected to Redis server!")
    except redis.ConnectionError:
        print("❌ Could not connect to Redis server on localhost:6379")
        print("   Please make sure Redis/Valkey is running")
        return None
    
    print()
    print("📋 Available functions:")
    print("   • test_compression(data, key='test') - Test data compression")
    print("   • compare_sizes(data) - Compare different data sizes")
    print("   • test_data_types() - Test various data types")
    print("   • memory_info(key) - Get memory usage for a key")
    print()
    
    return client

def test_compression(client, data, key='test'):
    """Test compression with given data"""
    # Store the data
    client.set(key, data)
    
    # Get memory usage
    memory = client.memory_usage(key)
    
    # Get the data back
    retrieved = client.get(key)
    
    print(f"Original data: {len(data)} bytes")
    print(f"Memory in Redis: {memory} bytes")
    print(f"Overhead: {memory - len(data)} bytes")
    print(f"Data matches: {retrieved == data.encode() if isinstance(data, str) else retrieved == data}")
    
    return memory

def compare_sizes(client):
    """Compare memory usage for different data sizes"""
    print("📊 Comparing memory usage for different data sizes:")
    print("-" * 50)
    
    sizes = [10, 50, 100, 500, 1000, 5000]
    
    for size in sizes:
        data = 'x' * size
        memory = test_compression(client, data, f'size_test_{size}')
        overhead = memory - size
        print(f"Size: {size:4d} bytes | Memory: {memory:4d} bytes | Overhead: {overhead:3d} bytes")
    
    print()

def test_data_types(client):
    """Test different data types"""
    print("🧪 Testing different data types:")
    print("-" * 40)
    
    # JSON data
    json_data = json.dumps({
        'users': [{'name': f'user{i}', 'id': i, 'active': True} for i in range(50)]
    })
    print("JSON data:")
    test_compression(client, json_data, 'json_test')
    print()
    
    # Repetitive text
    repetitive = "This is repetitive text. " * 100
    print("Repetitive text:")
    test_compression(client, repetitive, 'repetitive_test')
    print()
    
    # Random-ish data
    import random
    random_data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=1000))
    print("Random data:")
    test_compression(client, random_data, 'random_test')
    print()

def memory_info(client, key):
    """Get detailed memory info for a key"""
    try:
        memory = client.memory_usage(key)
        ttl = client.ttl(key)
        key_type = client.type(key).decode()
        
        print(f"Key: {key}")
        print(f"Type: {key_type}")
        print(f"Memory: {memory} bytes")
        print(f"TTL: {ttl} seconds" if ttl > 0 else "TTL: No expiration")
        
        return memory
    except Exception as e:
        print(f"Error getting info for key '{key}': {e}")
        return None

def interactive_session():
    """Start interactive session"""
    client = setup_redis_clients()
    if not client:
        return
    
    print("🎮 Interactive session ready!")
    print()
    print("Try these commands:")
    print(">>> test_compression(client, 'Hello, World!')")
    print(">>> compare_sizes(client)")
    print(">>> test_data_types(client)")
    print(">>> memory_info(client, 'test')")
    print()
    print("Or use Redis commands directly:")
    print(">>> client.set('mykey', 'myvalue')")
    print(">>> client.get('mykey')")
    print(">>> client.memory_usage('mykey')")
    print()
    print("Type your commands below. Use Ctrl+C to exit.")
    print()
    
    # Make functions available in the interactive session
    import code
    console_locals = {
        'client': client,
        'test_compression': lambda data, key='test': test_compression(client, data, key),
        'compare_sizes': lambda: compare_sizes(client),
        'test_data_types': lambda: test_data_types(client),
        'memory_info': lambda key: memory_info(client, key),
        'json': json,
    }
    
    try:
        code.interact(local=console_locals, banner="")
    except KeyboardInterrupt:
        print("\n👋 Closing session...")
    finally:
        client.close()
        print("✅ Session closed!")

if __name__ == "__main__":
    interactive_session()
