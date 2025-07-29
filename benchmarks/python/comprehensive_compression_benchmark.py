#!/usr/bin/env python3
# Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

import asyncio
import json
import time
from pathlib import Path
from statistics import mean
from typing import List, Dict, Any

from glide import (
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    CompressionConfiguration,
    CompressionBackend,
    Logger,
    LogLevel,
)


async def run_benchmark_scenario(
    host: str,
    port: int,
    data_size: int,
    operations: int,
    compression_config: CompressionConfiguration = None,
    scenario_name: str = "default"
) -> Dict[str, Any]:
    """Run a single benchmark scenario and return results."""
    
    config = GlideClientConfiguration(
        [NodeAddress(host=host, port=port)],
        compression=compression_config
    )
    
    client = await GlideClient.create(config)
    
    # Prepare test data
    test_data = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * (data_size // 56 + 1)
    test_data = test_data[:data_size]
    
    # Warm up
    for i in range(10):
        await client.set(f"warmup:{i}", test_data)
        await client.get(f"warmup:{i}")
    
    # Benchmark SET operations
    set_times = []
    start_time = time.perf_counter()
    
    for i in range(operations):
        op_start = time.perf_counter()
        await client.set(f"bench:set:{i}", test_data)
        op_end = time.perf_counter()
        set_times.append((op_end - op_start) * 1000)  # Convert to ms
    
    set_total_time = time.perf_counter() - start_time
    
    # Benchmark GET operations
    get_times = []
    start_time = time.perf_counter()
    
    for i in range(operations):
        op_start = time.perf_counter()
        await client.get(f"bench:set:{i}")
        op_end = time.perf_counter()
        get_times.append((op_end - op_start) * 1000)  # Convert to ms
    
    get_total_time = time.perf_counter() - start_time
    
    await client.close()
    
    # Calculate statistics
    def calc_percentile(times: List[float], percentile: float) -> float:
        times_sorted = sorted(times)
        index = int(len(times_sorted) * percentile / 100)
        return times_sorted[min(index, len(times_sorted) - 1)]
    
    return {
        "scenario": scenario_name,
        "data_size": data_size,
        "operations": operations,
        "compression_enabled": compression_config is not None and compression_config.enabled,
        "compression_backend": compression_config.backend.name if compression_config and compression_config.enabled else None,
        "compression_level": compression_config.compression_level if compression_config and compression_config.enabled else None,
        "min_compression_size": compression_config.min_compression_size if compression_config and compression_config.enabled else None,
        
        # SET operation metrics
        "set_total_time_sec": set_total_time,
        "set_ops_per_sec": operations / set_total_time,
        "set_avg_latency_ms": mean(set_times),
        "set_p50_latency_ms": calc_percentile(set_times, 50),
        "set_p90_latency_ms": calc_percentile(set_times, 90),
        "set_p99_latency_ms": calc_percentile(set_times, 99),
        
        # GET operation metrics
        "get_total_time_sec": get_total_time,
        "get_ops_per_sec": operations / get_total_time,
        "get_avg_latency_ms": mean(get_times),
        "get_p50_latency_ms": calc_percentile(get_times, 50),
        "get_p90_latency_ms": calc_percentile(get_times, 90),
        "get_p99_latency_ms": calc_percentile(get_times, 99),
    }


async def main():
    host = "localhost"
    port = 6379
    data_size = 5000  # 5KB of compressible data
    operations = 1000  # Number of operations per scenario
    
    Logger.set_logger_config(LogLevel.INFO, "compression_benchmark")
    
    print("🚀 Starting Comprehensive Compression Benchmark")
    print(f"   Data size: {data_size} bytes")
    print(f"   Operations per scenario: {operations}")
    print(f"   Target: {host}:{port}")
    print()
    
    results = []
    
    # Scenario 1: No compression (baseline)
    print("📊 Running baseline (no compression)...")
    baseline_result = await run_benchmark_scenario(
        host, port, data_size, operations, 
        compression_config=None,
        scenario_name="baseline_no_compression"
    )
    results.append(baseline_result)
    print(f"   SET: {baseline_result['set_ops_per_sec']:.0f} ops/sec, avg latency: {baseline_result['set_avg_latency_ms']:.2f}ms")
    print(f"   GET: {baseline_result['get_ops_per_sec']:.0f} ops/sec, avg latency: {baseline_result['get_avg_latency_ms']:.2f}ms")
    print()
    
    # Scenario 2-4: ZSTD with different compression levels
    for level in [1, 3, 6]:
        print(f"📊 Running ZSTD compression level {level}...")
        compression_config = CompressionConfiguration(
            enabled=True,
            backend=CompressionBackend.ZSTD,
            compression_level=level,
            min_compression_size=64
        )
        
        result = await run_benchmark_scenario(
            host, port, data_size, operations,
            compression_config=compression_config,
            scenario_name=f"zstd_level_{level}"
        )
        results.append(result)
        print(f"   SET: {result['set_ops_per_sec']:.0f} ops/sec, avg latency: {result['set_avg_latency_ms']:.2f}ms")
        print(f"   GET: {result['get_ops_per_sec']:.0f} ops/sec, avg latency: {result['get_avg_latency_ms']:.2f}ms")
        print()
    
    # Scenario 5: Different min compression size
    print("📊 Running ZSTD with higher min compression size (1000 bytes)...")
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=3,
        min_compression_size=1000
    )
    
    result = await run_benchmark_scenario(
        host, port, data_size, operations,
        compression_config=compression_config,
        scenario_name="zstd_min_1000"
    )
    results.append(result)
    print(f"   SET: {result['set_ops_per_sec']:.0f} ops/sec, avg latency: {result['set_avg_latency_ms']:.2f}ms")
    print(f"   GET: {result['get_ops_per_sec']:.0f} ops/sec, avg latency: {result['get_avg_latency_ms']:.2f}ms")
    print()
    
    # Save results
    results_file = "benchmarks/results/comprehensive_compression_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Results saved to: {results_file}")
    print()
    
    # Print summary comparison
    print("📈 Performance Summary (compared to baseline):")
    print("=" * 80)
    baseline_set_ops = baseline_result['set_ops_per_sec']
    baseline_get_ops = baseline_result['get_ops_per_sec']
    
    for result in results[1:]:  # Skip baseline
        set_ratio = result['set_ops_per_sec'] / baseline_set_ops
        get_ratio = result['get_ops_per_sec'] / baseline_get_ops
        
        print(f"{result['scenario']:20} | SET: {set_ratio:6.2%} | GET: {get_ratio:6.2%} | "
              f"SET latency: {result['set_avg_latency_ms']:5.2f}ms | GET latency: {result['get_avg_latency_ms']:5.2f}ms")


if __name__ == "__main__":
    asyncio.run(main())
