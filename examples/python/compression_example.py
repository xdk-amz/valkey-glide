"""
Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

This example demonstrates how to use automatic compression with Valkey GLIDE.
It shows various compression configurations and use cases.
"""

import asyncio
import json
import time
from typing import List, Tuple, Dict, Any

from glide import (
    GlideClient,
    GlideClusterClient,
    GlideClientConfiguration,
    GlideClusterClientConfiguration,
    CompressionConfiguration,
    CompressionBackend,
    Logger,
    LogLevel,
    NodeAddress,
)


async def create_client_with_compression(
    nodes_list: List[Tuple[str, int]] = [("localhost", 6379)],
    compression_config: CompressionConfiguration = None,
    use_cluster: bool = False
) -> GlideClient:
    """
    Creates a GlideClient with compression configuration.
    
    Args:
        nodes_list: List of (host, port) tuples for server addresses
        compression_config: Compression configuration to use
        use_cluster: Whether to create a cluster client
        
    Returns:
        GlideClient or GlideClusterClient instance
    """
    addresses = [NodeAddress(host, port) for host, port in nodes_list]
    
    if use_cluster:
        config = GlideClusterClientConfiguration(
            addresses=addresses,
            compression=compression_config,
            request_timeout=2000
        )
        return await GlideClusterClient.create(config)
    else:
        config = GlideClientConfiguration(
            addresses=addresses,
            compression=compression_config,
            request_timeout=2000
        )
        return await GlideClient.create(config)


async def basic_compression_example():
    """
    Demonstrates basic compression usage with default settings.
    """
    Logger.log(LogLevel.INFO, "compression_example", "=== Basic Compression Example ===")
    
    # Create compression configuration with defaults
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        # compression_level defaults to 3
        # min_compression_size defaults to 64 bytes
    )
    
    client = await create_client_with_compression(
        compression_config=compression_config
    )
    
    try:
        # Store some data that will be compressed
        large_json = {
            "user_id": "12345",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "preferences": {
                "theme": "dark",
                "language": "en",
                "notifications": True
            },
            "data": "x" * 1000  # Large field to ensure compression
        }
        
        json_str = json.dumps(large_json)
        Logger.log(LogLevel.INFO, "compression_example", f"Original JSON size: {len(json_str)} bytes")
        
        # Set the data (will be automatically compressed)
        await client.set("user:12345", json_str)
        Logger.log(LogLevel.INFO, "compression_example", "Data stored with compression")
        
        # Get the data (will be automatically decompressed)
        retrieved_data = await client.get("user:12345")
        retrieved_json = json.loads(retrieved_data.decode())
        
        Logger.log(LogLevel.INFO, "compression_example", f"Retrieved data matches: {retrieved_json == large_json}")
        Logger.log(LogLevel.INFO, "compression_example", f"Retrieved user: {retrieved_json['name']}")
        
    finally:
        await client.close()


async def compression_configuration_examples():
    """
    Demonstrates different compression configurations for various use cases.
    """
    Logger.log(LogLevel.INFO, "compression_example", "=== Compression Configuration Examples ===")
    
    # High-performance configuration (fast compression)
    high_performance_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=1,  # Fastest compression
        min_compression_size=128,  # Skip smaller values
        max_compression_size=1024 * 1024  # 1MB limit
    )
    
    # High-compression configuration (better compression ratio)
    high_compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=6,  # Better compression
        min_compression_size=32,  # Compress more values
        max_compression_size=None  # No size limit
    )
    
    # Balanced configuration (recommended for most use cases)
    balanced_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=3,  # Good balance
        min_compression_size=64,  # Standard threshold
        max_compression_size=10 * 1024 * 1024  # 10MB limit
    )
    
    configs = [
        ("High Performance", high_performance_config),
        ("High Compression", high_compression_config),
        ("Balanced", balanced_config)
    ]
    
    test_data = "The quick brown fox jumps over the lazy dog. " * 100  # ~4.3KB
    
    for config_name, config in configs:
        Logger.log(LogLevel.INFO, "compression_example", f"Testing {config_name} configuration")
        
        client = await create_client_with_compression(compression_config=config)
        
        try:
            # Measure compression performance
            start_time = time.time()
            await client.set(f"test:{config_name.lower().replace(' ', '_')}", test_data)
            set_time = time.time() - start_time
            
            start_time = time.time()
            retrieved = await client.get(f"test:{config_name.lower().replace(' ', '_')}")
            get_time = time.time() - start_time
            
            Logger.log(LogLevel.INFO, "compression_example", 
                      f"  Set time: {set_time*1000:.2f}ms, Get time: {get_time*1000:.2f}ms")
            Logger.log(LogLevel.INFO, "compression_example", 
                      f"  Data integrity: {retrieved.decode() == test_data}")
            
        finally:
            await client.close()


async def batch_operations_example():
    """
    Demonstrates compression with batch operations (pipelines and transactions).
    """
    Logger.log(LogLevel.INFO, "compression_example", "=== Batch Operations with Compression ===")
    
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        min_compression_size=32  # Lower threshold for demo
    )
    
    client = await create_client_with_compression(compression_config=compression_config)
    
    try:
        # Pipeline example
        Logger.log(LogLevel.INFO, "compression_example", "Testing pipeline with compression")
        
        pipeline_data = {
            "user:1": json.dumps({"name": "Alice", "data": "A" * 500}),
            "user:2": json.dumps({"name": "Bob", "data": "B" * 500}),
            "user:3": json.dumps({"name": "Charlie", "data": "C" * 500})
        }
        
        # Use pipeline to set multiple values (all will be compressed)
        async with client.pipeline() as pipeline:
            for key, value in pipeline_data.items():
                pipeline.set(key, value)
            pipeline.mget(list(pipeline_data.keys()))
            results = await pipeline.exec()
        
        Logger.log(LogLevel.INFO, "compression_example", f"Pipeline executed, got {len(results)} results")
        
        # The last result is from MGET - verify decompression worked
        mget_results = results[-1]
        for i, (key, original_value) in enumerate(pipeline_data.items()):
            retrieved_value = mget_results[i].decode()
            matches = retrieved_value == original_value
            Logger.log(LogLevel.INFO, "compression_example", f"  {key}: {matches}")
        
        # Transaction example
        Logger.log(LogLevel.INFO, "compression_example", "Testing transaction with compression")
        
        async with client.transaction() as transaction:
            transaction.set("counter:compressed", json.dumps({"count": 0, "data": "x" * 200}))
            transaction.get("counter:compressed")
            transaction.set("counter:compressed", json.dumps({"count": 1, "data": "x" * 200}))
            transaction.get("counter:compressed")
            tx_results = await transaction.exec()
        
        Logger.log(LogLevel.INFO, "compression_example", f"Transaction executed, got {len(tx_results)} results")
        
        # Verify the final counter value
        final_data = json.loads(tx_results[-1].decode())
        Logger.log(LogLevel.INFO, "compression_example", f"Final counter value: {final_data['count']}")
        
    finally:
        await client.close()


async def mixed_client_scenario():
    """
    Demonstrates compatibility between compression-enabled and disabled clients.
    """
    Logger.log(LogLevel.INFO, "compression_example", "=== Mixed Client Scenario ===")
    
    # Client with compression enabled
    compression_config = CompressionConfiguration(enabled=True)
    compressed_client = await create_client_with_compression(
        compression_config=compression_config
    )
    
    # Client with compression disabled
    uncompressed_client = await create_client_with_compression(
        compression_config=CompressionConfiguration(enabled=False)
    )
    
    try:
        test_data = "This is test data that will be compressed. " * 50
        
        # Store data with compression-enabled client
        await compressed_client.set("mixed:test", test_data)
        Logger.log(LogLevel.INFO, "compression_example", "Data stored with compression-enabled client")
        
        # Read with compression-enabled client (automatic decompression)
        compressed_read = await compressed_client.get("mixed:test")
        Logger.log(LogLevel.INFO, "compression_example", 
                  f"Compression-enabled client read: {compressed_read.decode() == test_data}")
        
        # Read with compression-disabled client (gets raw compressed data)
        uncompressed_read = await uncompressed_client.get("mixed:test")
        Logger.log(LogLevel.INFO, "compression_example", 
                  f"Compression-disabled client read raw data size: {len(uncompressed_read)} bytes")
        Logger.log(LogLevel.INFO, "compression_example", 
                  f"Raw data is different from original: {uncompressed_read != test_data.encode()}")
        
        # Store uncompressed data
        await uncompressed_client.set("mixed:uncompressed", test_data)
        Logger.log(LogLevel.INFO, "compression_example", "Data stored with compression-disabled client")
        
        # Read uncompressed data with both clients
        compressed_read_uncomp = await compressed_client.get("mixed:uncompressed")
        uncompressed_read_uncomp = await uncompressed_client.get("mixed:uncompressed")
        
        Logger.log(LogLevel.INFO, "compression_example", 
                  f"Both clients read uncompressed data correctly: "
                  f"{compressed_read_uncomp.decode() == test_data and uncompressed_read_uncomp.decode() == test_data}")
        
    finally:
        await compressed_client.close()
        await uncompressed_client.close()


async def performance_comparison():
    """
    Compares performance with and without compression.
    """
    Logger.log(LogLevel.INFO, "compression_example", "=== Performance Comparison ===")
    
    # Test data of different types
    test_cases = [
        ("Small JSON", json.dumps({"id": 1, "name": "test"})),
        ("Large JSON", json.dumps({"id": 1, "data": "x" * 2000, "metadata": {"created": "2024-01-01"}})),
        ("Repetitive Text", "Hello World! " * 200),
        ("Random-like Data", "".join(chr(65 + (i % 26)) for i in range(1000)))
    ]
    
    configs = [
        ("No Compression", CompressionConfiguration(enabled=False)),
        ("With Compression", CompressionConfiguration(enabled=True, min_compression_size=10))
    ]
    
    for test_name, test_data in test_cases:
        Logger.log(LogLevel.INFO, "compression_example", f"Testing: {test_name} ({len(test_data)} bytes)")
        
        for config_name, config in configs:
            client = await create_client_with_compression(compression_config=config)
            
            try:
                # Measure set performance
                start_time = time.time()
                await client.set(f"perf:{test_name.lower().replace(' ', '_')}", test_data)
                set_time = time.time() - start_time
                
                # Measure get performance
                start_time = time.time()
                retrieved = await client.get(f"perf:{test_name.lower().replace(' ', '_')}")
                get_time = time.time() - start_time
                
                # Verify data integrity
                data_matches = retrieved.decode() == test_data
                
                Logger.log(LogLevel.INFO, "compression_example", 
                          f"  {config_name}: SET {set_time*1000:.2f}ms, GET {get_time*1000:.2f}ms, "
                          f"Integrity: {data_matches}")
                
            finally:
                await client.close()
        
        Logger.log(LogLevel.INFO, "compression_example", "")


async def error_handling_example():
    """
    Demonstrates error handling with compression.
    """
    Logger.log(LogLevel.INFO, "compression_example", "=== Error Handling Example ===")
    
    try:
        # Try to create client with invalid configuration
        invalid_config = CompressionConfiguration(
            enabled=True,
            compression_level=100,  # Invalid level for ZSTD (max is 22)
        )
        
        client = await create_client_with_compression(compression_config=invalid_config)
        await client.close()
        
    except Exception as e:
        Logger.log(LogLevel.INFO, "compression_example", f"Expected configuration error: {type(e).__name__}")
    
    # Valid configuration with error handling
    compression_config = CompressionConfiguration(enabled=True)
    client = await create_client_with_compression(compression_config=compression_config)
    
    try:
        # Normal operation
        await client.set("error:test", "test data")
        result = await client.get("error:test")
        Logger.log(LogLevel.INFO, "compression_example", f"Normal operation successful: {result.decode()}")
        
        # Compression errors are handled gracefully by the client
        # (fallback to uncompressed data with warning logs)
        
    except Exception as e:
        Logger.log(LogLevel.ERROR, "compression_example", f"Unexpected error: {e}")
    finally:
        await client.close()


async def cluster_compression_example():
    """
    Demonstrates compression with cluster client.
    """
    Logger.log(LogLevel.INFO, "compression_example", "=== Cluster Compression Example ===")
    
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        min_compression_size=32
    )
    
    try:
        cluster_client = await create_client_with_compression(
            nodes_list=[("localhost", 7000)],  # Adjust for your cluster setup
            compression_config=compression_config,
            use_cluster=True
        )
        
        try:
            # Test compression with cluster operations
            cluster_data = {
                "cluster:user:1": json.dumps({"name": "Alice", "region": "us-east", "data": "A" * 300}),
                "cluster:user:2": json.dumps({"name": "Bob", "region": "us-west", "data": "B" * 300}),
                "cluster:user:3": json.dumps({"name": "Charlie", "region": "eu-west", "data": "C" * 300})
            }
            
            # Set data across cluster (values will be compressed)
            for key, value in cluster_data.items():
                await cluster_client.set(key, value)
            
            Logger.log(LogLevel.INFO, "compression_example", "Data stored across cluster with compression")
            
            # Retrieve data (values will be decompressed)
            retrieved_keys = list(cluster_data.keys())
            retrieved_values = await cluster_client.mget(retrieved_keys)
            
            for i, key in enumerate(retrieved_keys):
                original = cluster_data[key]
                retrieved = retrieved_values[i].decode() if retrieved_values[i] else None
                matches = retrieved == original
                Logger.log(LogLevel.INFO, "compression_example", f"  {key}: {matches}")
            
        finally:
            await cluster_client.close()
            
    except Exception as e:
        Logger.log(LogLevel.WARN, "compression_example", 
                  f"Cluster example skipped (cluster not available): {e}")


async def main():
    """
    Main function that runs all compression examples.
    """
    Logger.set_logger_config(LogLevel.INFO)
    
    Logger.log(LogLevel.INFO, "compression_example", "Starting Valkey GLIDE Compression Examples")
    Logger.log(LogLevel.INFO, "compression_example", "=" * 60)
    
    try:
        await basic_compression_example()
        await compression_configuration_examples()
        await batch_operations_example()
        await mixed_client_scenario()
        await performance_comparison()
        await error_handling_example()
        await cluster_compression_example()
        
    except Exception as e:
        Logger.log(LogLevel.ERROR, "compression_example", f"Example failed: {e}")
        raise
    
    Logger.log(LogLevel.INFO, "compression_example", "=" * 60)
    Logger.log(LogLevel.INFO, "compression_example", "All compression examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
