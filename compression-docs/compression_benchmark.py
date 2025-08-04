#!/usr/bin/env python3
"""
Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

Comprehensive Python benchmark for GLIDE client compression performance.

This benchmark tests:
1. Various realistic data types (JSON, logs, CSV, XML, etc.)
2. Different compression levels and their impact on TPS
3. Memory usage comparison between compressed and uncompressed
4. Throughput measurements for different data sizes
5. Compression effectiveness across different data patterns
"""

import asyncio
import json
import os
import statistics
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the python directory to the path to import glide
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python', 'python'))

from glide import (
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    CompressionConfiguration,
    CompressionBackend,
)


class CompressionBenchmark:
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.host = host
        self.port = port
        self.warmup_iterations = 100
        self.benchmark_iterations = 1000
        self.tps_test_duration_ms = 5000  # 5 seconds
        
    def load_test_datasets(self) -> Dict[str, List[str]]:
        """Load standardized test datasets from files"""
        print("📊 Loading standardized test datasets...")
        
        datasets = {}
        data_dir = Path(__file__).parent.parent / "benchmarks" / "data"
        
        # Load datasets from standardized files
        datasets["json_objects"] = self._load_dataset_from_file(data_dir / "json_objects.txt", False)
        datasets["app_logs"] = self._load_dataset_from_file(data_dir / "app_logs.txt", False)
        datasets["csv_data"] = self._load_dataset_from_file(data_dir / "csv_data.txt", False)
        datasets["xml_docs"] = self._load_dataset_from_file(data_dir / "xml_docs.txt", True)  # XML uses --- separator
        datasets["base64"] = self._load_dataset_from_file(data_dir / "base64_data.txt", False)
        datasets["repetitive"] = self._load_dataset_from_file(data_dir / "repetitive_text.txt", False)
        datasets["random"] = self._load_dataset_from_file(data_dir / "random_data.txt", False)
        datasets["mixed_web"] = self._load_dataset_from_file(data_dir / "mixed_web.txt", True)  # Mixed web uses --- separator
        
        # Print dataset info
        for name, values in datasets.items():
            total_size = sum(len(value) for value in values)
            avg_size = total_size // len(values) if values else 0
            print(f"  {name:<12}: {len(values):3d} entries, {total_size:8,d} total bytes, {avg_size:5,d} avg bytes")
        
        print()
        return datasets
    
    def _load_dataset_from_file(self, filename: Path, use_separator: bool) -> List[str]:
        """Load dataset from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if use_separator:
                # Split by --- separator for XML and mixed web content
                parts = content.split('---')
                entries = [part.strip() for part in parts if part.strip()]
            else:
                # Split by lines for other formats
                lines = content.split('\n')
                entries = [line.strip() for line in lines if line.strip()]
            
            return entries
            
        except Exception as e:
            print(f"⚠️ Failed to load {filename}: {type(e).__name__} - {e}")
            print(f"   Using fallback generated data for this dataset")
            return self._generate_fallback_data(filename.name)
    
    def _generate_fallback_data(self, filename: str) -> List[str]:
        """Generate fallback data if file loading fails"""
        return [f"Fallback data entry {i} for {filename}" for i in range(10)]
    
    async def benchmark_compression_levels(self, datasets: Dict[str, List[str]]):
        """Benchmark different compression levels"""
        print("🎚️ Compression Level Benchmark")
        print("-" * 80)
        print(f"{'Level':<6} {'Dataset':<12} {'Original':<10} {'Compressed':<10} {'Ratio':<8} {'TPS':<8}")
        print("-" * 80)
        
        levels = [1, 3, 6, 9, 15, 22]
        test_dataset = datasets["json_objects"]  # Use JSON for level testing
        
        for level in levels:
            result = await self._benchmark_configuration(
                self._create_compression_config(CompressionBackend.ZSTD, level, 64),
                "json_objects", test_dataset
            )
            
            original_size = sum(len(data) for data in test_dataset)
            print(f"{level:<6d} {'json_objects':<12} {original_size:10,d} {result.compressed_size:10,d} {result.compression_ratio:<8.2f} {result.tps:8,.0f}")
        
        print()
    
    async def benchmark_data_types(self, datasets: Dict[str, List[str]]):
        """Benchmark different data types"""
        print("📋 Data Type Compression Effectiveness")
        print("   Measures compression ratio and memory savings for different data types")
        print("-" * 80)
        print(f"{'Dataset':<12} {'Entries':<8} {'Original':<10} {'Redis Mem':<10} {'Ratio':<8} {'TPS':<8} {'Savings':<10}")
        print("-" * 80)
        
        config = self._create_compression_config(CompressionBackend.ZSTD, 1, 64)
        
        for dataset_name, data in datasets.items():
            result = await self._benchmark_configuration(config, dataset_name, data)
            original_size = sum(len(entry) for entry in data)
            savings = ((original_size - result.compressed_size) / original_size) * 100
            
            print(f"{dataset_name:<12} {len(data):8,d} {original_size:10,d} {result.compressed_size:10,d} {result.compression_ratio:<8.2f} {result.tps:8,.0f} {savings:9.1f}%")
        
        print()
    
    async def benchmark_throughput(self, datasets: Dict[str, List[str]]):
        """Benchmark throughput with different configurations"""
        print("⚡ Throughput Benchmark (Operations/Second)")
        print("   Measures performance impact of compression on SET/GET operations")
        print("-" * 80)
        print(f"{'Dataset':<12} {'Uncompressed':<12} {'Compressed':<12} {'Perf Impact':<12}")
        print("-" * 80)
        
        compressed_config = self._create_compression_config(CompressionBackend.ZSTD, 1, 64)
        
        for dataset_name, data in datasets.items():
            # Benchmark uncompressed
            uncompressed = await self._benchmark_configuration(None, f"{dataset_name}_uncomp", data)
            
            # Benchmark compressed
            compressed = await self._benchmark_configuration(compressed_config, f"{dataset_name}_comp", data)
            
            difference = ((compressed.tps - uncompressed.tps) / uncompressed.tps) * 100
            
            print(f"{dataset_name:<12} {uncompressed.tps:12,.0f} {compressed.tps:12,.0f} {difference:+11.1f}%")
        
        print()
    
    async def benchmark_memory_efficiency(self, datasets: Dict[str, List[str]]):
        """Benchmark memory efficiency"""
        print("💾 Memory Efficiency Benchmark")
        print("-" * 80)
        print(f"{'Dataset':<12} {'Entries':<8} {'Original':<10} {'Uncomp Mem':<10} {'Comp Mem':<10} {'Mem Saved':<10}")
        print("-" * 80)
        
        compressed_config = self._create_compression_config(CompressionBackend.ZSTD, 1, 64)
        
        for dataset_name, data in datasets.items():
            # Test uncompressed memory usage
            uncompressed_memory = await self._measure_memory_usage(None, f"{dataset_name}_mem_uncomp", data)
            
            # Test compressed memory usage
            compressed_memory = await self._measure_memory_usage(compressed_config, f"{dataset_name}_mem_comp", data)
            
            original_size = sum(len(entry) for entry in data)
            memory_saved = ((uncompressed_memory - compressed_memory) / uncompressed_memory) * 100 if uncompressed_memory > 0 else 0
            
            print(f"{dataset_name:<12} {len(data):8,d} {original_size:10,d} {uncompressed_memory:10,d} {compressed_memory:10,d} {memory_saved:9.1f}%")
        
        print()
    
    async def _benchmark_configuration(self, compression_config: Optional[CompressionConfiguration], 
                                     key_prefix: str, data_list: List[str]) -> 'BenchmarkResult':
        """Benchmark a specific configuration"""
        
        config_builder = GlideClientConfiguration(
            addresses=[NodeAddress(host=self.host, port=self.port)]
        )
        
        if compression_config:
            config_builder.compression = compression_config
        
        client = await GlideClient.create(config_builder)
        
        try:
            # Warmup - use different entries for each warmup iteration
            for i in range(self.warmup_iterations):
                data = data_list[i % len(data_list)]
                await client.set(f"{key_prefix}_warmup_{i}", data)
            
            # Measure TPS
            start_time = time.time()
            operations = 0
            
            while (time.time() - start_time) * 1000 < self.tps_test_duration_ms:
                data = data_list[operations % len(data_list)]
                await client.set(f"{key_prefix}_tps_{operations}", data)
                await client.get(f"{key_prefix}_tps_{operations}")
                operations += 2  # SET + GET
            
            end_time = time.time()
            tps = operations / (end_time - start_time)
            
            # Measure compression across all entries
            total_compressed_size = 0
            original_size = 0
            
            for i, data in enumerate(data_list):
                test_key = f"{key_prefix}_size_test_{i}"
                await client.set(test_key, data)
                memory_usage = await self._get_memory_usage(test_key, client)
                total_compressed_size += memory_usage
                original_size += len(data)
            
            # Handle case where memory usage couldn't be measured
            if total_compressed_size == 0:
                total_compressed_size = original_size  # Fallback to original size
            
            # For uncompressed data, ratio should be 1.0
            if compression_config is None:
                compression_ratio = 1.0  # No compression applied
            else:
                compression_ratio = original_size / total_compressed_size if total_compressed_size > 0 else 1.0
            
            return BenchmarkResult(tps, total_compressed_size, compression_ratio)
            
        finally:
            await client.close()
    
    async def _measure_memory_usage(self, compression_config: Optional[CompressionConfiguration], 
                                   key_prefix: str, data_list: List[str]) -> int:
        """Measure memory usage for a configuration"""
        
        config_builder = GlideClientConfiguration(
            addresses=[NodeAddress(host=self.host, port=self.port)]
        )
        
        if compression_config:
            config_builder.compression = compression_config
        
        client = await GlideClient.create(config_builder)
        
        try:
            total_memory = 0
            for i, data in enumerate(data_list):
                key = f"{key_prefix}_{i}"
                await client.set(key, data)
                total_memory += await self._get_memory_usage(key, client)
            return total_memory
            
        finally:
            await client.close()
    
    def _create_compression_config(self, backend: CompressionBackend, level: int, min_size: int) -> CompressionConfiguration:
        """Create compression configuration"""
        return CompressionConfiguration(
            enabled=True,
            backend=backend,
            compression_level=level,
            min_compression_size=min_size
        )
    
    async def _get_memory_usage(self, key: str, client: GlideClient) -> int:
        """Get memory usage for a key"""
        try:
            result = await client.custom_command(["MEMORY", "USAGE", key])
            return int(result) if result is not None else 0
        except Exception:
            return 0


class BenchmarkResult:
    def __init__(self, tps: float, compressed_size: int, compression_ratio: float):
        self.tps = tps
        self.compressed_size = compressed_size
        self.compression_ratio = compression_ratio


async def main():
    print("🚀 GLIDE Python Compression Benchmark")
    print("=" * 61)
    print(f"Warmup iterations: 100")
    print(f"Benchmark iterations: 1000")
    print(f"TPS test duration: 5000ms")
    print()
    
    try:
        benchmark = CompressionBenchmark()
        
        # Load standardized test datasets
        datasets = benchmark.load_test_datasets()
        
        # Run comprehensive benchmarks
        await benchmark.benchmark_compression_levels(datasets)
        await benchmark.benchmark_data_types(datasets)
        await benchmark.benchmark_throughput(datasets)
        await benchmark.benchmark_memory_efficiency(datasets)
        
        print("\n🎉 Benchmark completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during benchmark: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
