#!/usr/bin/env python3
# Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

"""
Compression Feature Demo

This script demonstrates the compression feature in Valkey GLIDE Python client,
showing configuration options, performance comparison, compression ratios, and storage savings.
"""

import asyncio
import time
import redis
import random
import string
import json
from glide import (
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    CompressionConfiguration,
    CompressionBackend,
)


async def get_redis_memory_usage(key: str) -> int:
    """Get the memory usage of a key in Redis using direct redis-py client"""
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=False)
        memory_usage = redis_client.memory_usage(key)
        redis_client.close()
        return memory_usage if memory_usage else 0
    except Exception as e:
        print(f"   ⚠️  Could not get memory usage: {e}")
        return 0


def generate_realistic_json(target_size_kb: float = 1.0) -> str:
    """Generate realistic JSON data with varied fields and no duplication"""
    target_size = int(target_size_kb * 1024)
    
    # Base structure with realistic field names and types
    data = {
        "user_id": random.randint(100000, 999999),
        "username": f"user_{random.randint(1000, 9999)}",
        "email": f"user{random.randint(1000, 9999)}@example.com",
        "created_at": "2024-01-15T10:30:00Z",
        "last_login": "2024-01-20T14:22:33Z",
        "profile": {
            "first_name": random.choice(["John", "Jane", "Alice", "Bob", "Charlie", "Diana"]),
            "last_name": random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]),
            "age": random.randint(18, 80),
            "location": {
                "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                "country": "US",
                "timezone": random.choice(["EST", "PST", "CST", "MST"])
            }
        },
        "preferences": {
            "theme": random.choice(["dark", "light", "auto"]),
            "language": random.choice(["en", "es", "fr", "de"]),
            "notifications": {
                "email": random.choice([True, False]),
                "push": random.choice([True, False]),
                "sms": random.choice([True, False])
            }
        },
        "activity": []
    }
    
    # Add activity entries to reach target size
    activities = [
        "login", "logout", "view_profile", "update_settings", "send_message",
        "create_post", "like_post", "comment", "share", "upload_file"
    ]
    
    current_json = json.dumps(data, separators=(',', ':'))
    
    # Add activities until we reach target size
    activity_id = 1
    while len(current_json) < target_size:
        activity = {
            "id": activity_id,
            "action": random.choice(activities),
            "timestamp": f"2024-01-{random.randint(10, 20):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}Z",
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "user_agent": f"Mozilla/5.0 (Platform{random.randint(1, 100)}) Browser/{random.randint(1, 20)}.{random.randint(0, 9)}",
            "session_id": f"sess_{random.randint(100000, 999999)}_{random.randint(1000, 9999)}"
        }
        data["activity"].append(activity)
        activity_id += 1
        current_json = json.dumps(data, separators=(',', ':'))
        
        # Prevent infinite loop
        if activity_id > 1000:
            break
    
    return current_json


def generate_truly_random_data(size_bytes: int = 1024) -> str:
    """Generate truly random data that should not compress well"""
    # Use a mix of all printable ASCII characters for true randomness
    chars = string.ascii_letters + string.digits + string.punctuation + ' '
    return ''.join(random.choice(chars) for _ in range(size_bytes))


def generate_distributed_pattern(size_bytes: int = 1024) -> str:
    """Generate a pattern that's repetitive but more distributed"""
    # Create a base pattern with some structure but variation
    patterns = [
        "ERROR: Connection timeout to server",
        "INFO: User authentication successful", 
        "WARN: High memory usage detected",
        "DEBUG: Processing request batch",
        "ERROR: Database connection failed",
        "INFO: Cache invalidation completed",
        "WARN: Disk space running low",
        "DEBUG: API response time exceeded"
    ]
    
    result = []
    current_size = 0
    
    while current_size < size_bytes:
        # Pick a random pattern and add some variation
        base_pattern = random.choice(patterns)
        timestamp = f"2024-01-{random.randint(10, 20)} {random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
        thread_id = f"thread-{random.randint(1, 50)}"
        
        line = f"[{timestamp}] [{thread_id}] {base_pattern} (id: {random.randint(1000, 9999)})\n"
        result.append(line)
        current_size += len(line)
    
    return ''.join(result)[:size_bytes]


async def demonstrate_compression():
    print("🚀 Valkey GLIDE Compression Demo")
    print("=" * 50)
    
    # Generate realistic test cases
    print("🔄 Generating realistic test data...")
    
    test_cases = [
        ("Highly Compressible Text", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50),
        ("Realistic JSON Data", generate_realistic_json(1.0)),  # ~1KB JSON
        ("Distributed Log Pattern", generate_distributed_pattern(1024)),  # ~1KB logs
        ("Truly Random Data", generate_truly_random_data(1024)),  # ~1KB random
    ]
    
    print("📊 Test Data Overview:")
    for name, data in test_cases:
        print(f"   • {name}: {len(data)} bytes")
    print()
    
    # Test compression effectiveness for different data types
    print("🗜️  Compression Effectiveness Analysis")
    print("=" * 50)
    
    compression_results = []
    
    for case_name, test_data in test_cases:
        print(f"\n📋 Testing: {case_name}")
        print(f"   Original size: {len(test_data)} bytes")
        
        # Configuration without compression
        config_no_compression = GlideClientConfiguration(
            [NodeAddress(host="localhost", port=6379)]
        )
        
        # Configuration with compression (level 3)
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
        client_no_compression = await GlideClient.create(config_no_compression)
        key_no_compression = f"test:no_compression:{case_name.replace(' ', '_').lower()}"
        
        await client_no_compression.set(key_no_compression, test_data)
        memory_no_compression = await get_redis_memory_usage(key_no_compression)
        
        # Verify data integrity
        result_no_compression = await client_no_compression.get(key_no_compression)
        if isinstance(result_no_compression, bytes):
            result_no_compression = result_no_compression.decode('utf-8')
        
        await client_no_compression.close()
        
        # Test with compression
        client_with_compression = await GlideClient.create(config_with_compression)
        key_with_compression = f"test:with_compression:{case_name.replace(' ', '_').lower()}"
        
        await client_with_compression.set(key_with_compression, test_data)
        memory_with_compression = await get_redis_memory_usage(key_with_compression)
        
        # Verify data integrity
        result_with_compression = await client_with_compression.get(key_with_compression)
        if isinstance(result_with_compression, bytes):
            result_with_compression = result_with_compression.decode('utf-8')
        
        await client_with_compression.close()
        
        # Calculate compression metrics
        data_integrity = result_no_compression == test_data and result_with_compression == test_data
        
        if memory_no_compression > 0 and memory_with_compression > 0:
            compression_ratio = memory_no_compression / memory_with_compression
            space_saved = memory_no_compression - memory_with_compression
            space_saved_percent = (space_saved / memory_no_compression) * 100
            
            print(f"   Without compression: {memory_no_compression} bytes in Redis")
            print(f"   With compression: {memory_with_compression} bytes in Redis")
            print(f"   Compression ratio: {compression_ratio:.2f}:1")
            print(f"   Space saved: {space_saved} bytes ({space_saved_percent:.1f}%)")
            print(f"   Data integrity: {'✅ PASS' if data_integrity else '❌ FAIL'}")
            
            compression_results.append({
                'name': case_name,
                'original_size': len(test_data),
                'uncompressed_redis_size': memory_no_compression,
                'compressed_redis_size': memory_with_compression,
                'compression_ratio': compression_ratio,
                'space_saved': space_saved,
                'space_saved_percent': space_saved_percent,
                'data_integrity': data_integrity
            })
        else:
            print(f"   ⚠️  Could not measure Redis memory usage")
            print(f"   Data integrity: {'✅ PASS' if data_integrity else '❌ FAIL'}")
    
    print(f"\n📊 Compression Summary")
    print("=" * 50)
    total_original = sum(r['uncompressed_redis_size'] for r in compression_results)
    total_compressed = sum(r['compressed_redis_size'] for r in compression_results)
    
    if total_original > 0:
        overall_ratio = total_original / total_compressed
        overall_saved = total_original - total_compressed
        overall_saved_percent = (overall_saved / total_original) * 100
        
        print(f"Overall compression ratio: {overall_ratio:.2f}:1")
        print(f"Total space saved: {overall_saved} bytes ({overall_saved_percent:.1f}%)")
        print()
        
        print("Per data type breakdown:")
        for result in compression_results:
            print(f"   • {result['name']}: {result['compression_ratio']:.2f}:1 ratio, {result['space_saved_percent']:.1f}% saved")
    
    print()
    
    # Performance comparison with a representative dataset
    print("⚡ Performance Comparison")
    print("=" * 50)
    
    # Use the most compressible data for performance testing
    perf_test_data = test_cases[0][1]  # Highly compressible text
    print(f"Using test data: {len(perf_test_data)} bytes of highly compressible text")
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
    print("🔄 Performance test WITHOUT compression...")
    client_no_compression = await GlideClient.create(config_no_compression)
    
    start_time = time.perf_counter()
    for i in range(100):
        await client_no_compression.set(f"perf:no_compression:{i}", perf_test_data)
    
    for i in range(100):
        result = await client_no_compression.get(f"perf:no_compression:{i}")
        # Convert bytes to string for comparison
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert result == perf_test_data, f"Data mismatch at key {i}"
    
    no_compression_time = time.perf_counter() - start_time
    await client_no_compression.close()
    
    print(f"   ✅ Completed 200 operations in {no_compression_time:.3f} seconds")
    print(f"   📈 Rate: {200/no_compression_time:.0f} ops/sec")
    
    # Test with compression
    print("🗜️  Performance test WITH compression (ZSTD level 3)...")
    client_with_compression = await GlideClient.create(config_with_compression)
    
    start_time = time.perf_counter()
    for i in range(100):
        await client_with_compression.set(f"perf:with_compression:{i}", perf_test_data)
    
    for i in range(100):
        result = await client_with_compression.get(f"perf:with_compression:{i}")
        # Convert bytes to string for comparison
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert result == perf_test_data, f"Data mismatch at key {i}"
    
    compression_time = time.perf_counter() - start_time
    await client_with_compression.close()
    
    print(f"   ✅ Completed 200 operations in {compression_time:.3f} seconds")
    print(f"   📈 Rate: {200/compression_time:.0f} ops/sec")
    
    # Compare results
    print(f"\n📊 Performance Summary:")
    if compression_time < no_compression_time:
        improvement = ((no_compression_time - compression_time) / no_compression_time) * 100
        print(f"   🎉 Compression is {improvement:.1f}% FASTER!")
    else:
        overhead = ((compression_time - no_compression_time) / no_compression_time) * 100
        print(f"   ⚠️  Compression has {overhead:.1f}% overhead")
    
    print(f"   📉 Time difference: {abs(compression_time - no_compression_time):.3f} seconds")
    print()
    
    # Demonstrate different compression levels with storage analysis
    print("🔧 Compression Level Analysis")
    print("=" * 50)
    
    # Use a mix of data types to better show compression level differences
    mixed_test_data = test_cases[1][1] + test_cases[2][1]  # JSON + Log data
    print(f"Testing compression levels with {len(mixed_test_data)} bytes of mixed data (JSON + logs)")
    print()
    
    # First, get baseline without compression for comparison
    print("📊 Testing Baseline (No Compression)...")
    config_no_compression = GlideClientConfiguration(
        [NodeAddress(host="localhost", port=6379)]
    )
    
    client_baseline = await GlideClient.create(config_no_compression)
    baseline_key = "level_test_baseline"
    
    # Performance test for baseline
    start_time = time.perf_counter()
    for i in range(50):
        await client_baseline.set(f"{baseline_key}:{i}", mixed_test_data)
        result = await client_baseline.get(f"{baseline_key}:{i}")
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert result == mixed_test_data, f"Data mismatch at baseline, key {i}"
    
    baseline_time = time.perf_counter() - start_time
    
    # Storage test for baseline
    await client_baseline.set(baseline_key, mixed_test_data)
    baseline_memory = await get_redis_memory_usage(baseline_key)
    await client_baseline.close()
    
    baseline_ops_per_sec = 100 / baseline_time
    print(f"   Performance: {baseline_ops_per_sec:.0f} ops/sec ({baseline_time:.3f}s for 100 ops)")
    print(f"   Storage: {baseline_memory} bytes in Redis")
    print()
    
    level_results = []
    
    for level in [1, 3, 6]:
        print(f"📊 Testing ZSTD Level {level}...")
        
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
        key = f"level_test_compression_{level}"  # Unique key for each level
        
        # Performance test
        start_time = time.perf_counter()
        for i in range(50):
            await client.set(f"{key}:{i}", mixed_test_data)
            result = await client.get(f"{key}:{i}")
            # Convert bytes to string for comparison
            if isinstance(result, bytes):
                result = result.decode('utf-8')
            assert result == mixed_test_data, f"Data mismatch at level {level}, key {i}"
        
        level_time = time.perf_counter() - start_time
        
        # Storage test - use a unique key for memory measurement
        await client.set(key, mixed_test_data)
        memory_usage = await get_redis_memory_usage(key)
        
        await client.close()
        
        ops_per_sec = 100 / level_time
        
        print(f"   Performance: {ops_per_sec:.0f} ops/sec ({level_time:.3f}s for 100 ops)")
        if memory_usage > 0:
            print(f"   Storage: {memory_usage} bytes in Redis")
            
            level_results.append({
                'level': level,
                'ops_per_sec': ops_per_sec,
                'time': level_time,
                'memory_usage': memory_usage
            })
        else:
            print(f"   Storage: Could not measure")
        print()
    
    # Compare compression levels
    if level_results and baseline_memory > 0:
        print("📈 Compression Level Comparison (vs Baseline No Compression):")
        print("-" * 60)
        
        for result in level_results:
            level = result['level']
            perf_vs_baseline = (result['ops_per_sec'] / baseline_ops_per_sec) * 100
            
            if result['memory_usage'] > 0:
                compression_ratio = baseline_memory / result['memory_usage']
                storage_saved = ((baseline_memory - result['memory_usage']) / baseline_memory) * 100
                
                print(f"   Level {level}: {perf_vs_baseline:.0f}% performance, {compression_ratio:.2f}:1 compression, {storage_saved:.1f}% storage saved")
            else:
                print(f"   Level {level}: {perf_vs_baseline:.0f}% performance vs baseline")
        
        print()
        print("📊 Level-to-Level Storage Comparison:")
        print("-" * 40)
        
        # Also compare levels against each other
        level_1_result = next((r for r in level_results if r['level'] == 1), None)
        if level_1_result:
            for result in level_results:
                if result['level'] == 1:
                    continue
                level = result['level']
                if level_1_result['memory_usage'] > 0 and result['memory_usage'] > 0:
                    ratio_vs_level1 = level_1_result['memory_usage'] / result['memory_usage']
                    additional_savings = ((level_1_result['memory_usage'] - result['memory_usage']) / level_1_result['memory_usage']) * 100
                    perf_vs_level1 = (result['ops_per_sec'] / level_1_result['ops_per_sec']) * 100
                    
                    print(f"   Level {level} vs Level 1: {ratio_vs_level1:.2f}:1 better compression, {additional_savings:+.1f}% more storage saved, {perf_vs_level1:.0f}% performance")
    elif level_results:
        print("📈 Compression Level Performance Comparison:")
        print("-" * 40)
        
        # Find baseline (level 1) for comparison
        baseline = next((r for r in level_results if r['level'] == 1), level_results[0])
        
        for result in level_results:
            level = result['level']
            perf_vs_baseline = (result['ops_per_sec'] / baseline['ops_per_sec']) * 100
            print(f"   Level {level}: {perf_vs_baseline:.0f}% performance vs Level 1")
    
    print()
    print("✨ Demo completed successfully!")
    print()
    print("💡 Key Insights:")
    print("   🗜️  Compression Effectiveness:")
    print("      • Different data types compress at different ratios")
    print("      • Repetitive/structured data compresses better")
    print("      • Actual storage savings measured in Redis")
    print()
    print("   ⚡ Performance Trade-offs:")
    print("      • Level 1: Fastest compression, moderate space savings")
    print("      • Level 3: Balanced compression and speed (default)")
    print("      • Level 6: Best compression, slower performance")
    print()
    print("   🎯 Recommendations:")
    print("      • Use compression for data >64 bytes")
    print("      • Choose level based on CPU vs storage priorities")
    print("      • Monitor actual compression ratios for your data")
    print("      • Consider network bandwidth savings in distributed setups")


if __name__ == "__main__":
    asyncio.run(demonstrate_compression())
