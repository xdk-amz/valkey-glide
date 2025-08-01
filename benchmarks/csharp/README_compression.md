# C# Compression Benchmark

This directory contains a comprehensive compression benchmark for the GLIDE C# client, following the same test format and dataset as the Python, Java, and Go benchmarks.

## Overview

The C# compression benchmark tests:
1. Various realistic data types (JSON, logs, CSV, XML, etc.)
2. Different compression levels and their impact on TPS
3. Memory usage comparison between compressed and uncompressed
4. Throughput measurements for different data sizes
5. Compression effectiveness across different data patterns

## Files

- `CompressionBenchmark.cs` - Main benchmark implementation
- `CompressionBenchmark.csproj` - .NET project file with dependencies
- `run_compression_benchmark.sh` - Shell script to run the benchmark
- `README_compression.md` - This documentation file

## Prerequisites

1. **.NET SDK**: Make sure .NET 6.0 or 8.0 SDK is installed
2. **Redis/Valkey Server**: A running Redis or Valkey server on localhost:6379
3. **Dependencies**: The benchmark uses the same datasets as other language benchmarks

## Usage

### Quick Start

```bash
# Make sure you're in the benchmarks/csharp directory
cd benchmarks/csharp

# Run the benchmark using the shell script
./run_compression_benchmark.sh
```

### Manual Execution

```bash
# Restore dependencies
dotnet restore CompressionBenchmark.csproj

# Build the project
dotnet build CompressionBenchmark.csproj -c Release

# Run the benchmark
dotnet run --project CompressionBenchmark.csproj -c Release
```

### Using Makefile (if available)

```bash
make compression-benchmark
```

## Benchmark Types

### 1. 🎚️ Compression Level Benchmark
Tests ZSTD compression levels 1, 3, 6, 9, 15, 22 using JSON objects dataset:
- Measures compression ratio improvement with higher levels
- Shows TPS impact of different compression levels
- Demonstrates trade-off between compression effectiveness and performance

### 2. 📋 Data Type Compression Effectiveness
Tests all 8 data types with ZSTD level 1:
- JSON objects, application logs, CSV data, XML documents
- Base64 data, repetitive text, random data, mixed web content
- Shows compression ratio, memory savings, and TPS for each data type

### 3. ⚡ Throughput Benchmark
Compares performance impact of compression:
- Measures TPS for compressed vs uncompressed operations
- Shows percentage performance impact
- Helps understand compression overhead

### 4. 💾 Memory Efficiency Benchmark
Measures actual Redis memory usage:
- Compares memory consumption with and without compression
- Shows memory savings percentage
- Demonstrates real-world storage benefits

## Test Datasets

The benchmark uses standardized datasets from `../data/`:

- **json_objects**: JSON data structures
- **app_logs**: Application log entries
- **csv_data**: Comma-separated values
- **xml_docs**: XML documents (uses `---` separator)
- **base64**: Base64-encoded data
- **repetitive**: Highly repetitive text
- **random**: Random data (low compressibility)
- **mixed_web**: Mixed web content (uses `---` separator)

## Configuration

The benchmark uses these default settings:
- **Host**: localhost
- **Port**: 6379
- **Warmup iterations**: 100
- **Benchmark iterations**: 1000
- **TPS test duration**: 5000ms
- **Default compression**: ZSTD level 1, 64-byte minimum

## Sample Output

```
🚀 GLIDE C# Compression Benchmark
=============================================================
Warmup iterations: 100
Benchmark iterations: 1000
TPS test duration: 5000ms

📊 Loading standardized test datasets...
  json_objects:  20 entries,   14,373 total bytes,   718 avg bytes
  app_logs    :   9 entries,    5,245 total bytes,   582 avg bytes
  ...

🎚️ Compression Level Benchmark
--------------------------------------------------------------------------------
Level  Dataset      Original   Compressed Ratio    TPS     
--------------------------------------------------------------------------------
1      json_objects     14,373        6,763  2.12   24,456
3      json_objects     14,373        5,749  2.50   23,815
...

📋 Data Type Compression Effectiveness
   Measures compression ratio and memory savings for different data types
--------------------------------------------------------------------------------
Dataset      Entries  Original   Redis Mem  Ratio    TPS      Savings   
--------------------------------------------------------------------------------
json_objects      20    14,373       5,749   2.50   22,228      60.0%
repetitive        12    10,599       1,324   8.00   22,442      87.5%
...
```

## Dependencies

- **Valkey.Glide**: The GLIDE C# client library
- **System.Text.Json**: For JSON serialization (built-in)
- **.NET 6.0/8.0**: Runtime and SDK

## Troubleshooting

### Common Issues

1. **"Redis/Valkey server not running"**
   - Start Redis: `redis-server`
   - Or start Valkey: `valkey-server`

2. **".NET is not installed"**
   - Install .NET SDK from https://dotnet.microsoft.com/download

3. **"Failed to restore dependencies"**
   - Check internet connection
   - Verify project file is correct
   - Try: `dotnet nuget locals all --clear`

4. **"CompressionBenchmark.cs not found"**
   - Make sure you're in the `benchmarks/csharp` directory
   - Check that all files were copied correctly

### Performance Notes

- Results may vary based on system performance
- Ensure Redis/Valkey server has sufficient memory
- Close other applications for consistent results
- Run multiple times and average results for accuracy

## Cross-Language Comparison

This C# benchmark produces identical output format to:
- Python compression benchmark (`benchmarks/python/`)
- Java compression benchmark (`benchmarks/java/`)
- Go compression benchmark (`benchmarks/go/`)

All benchmarks use the same datasets and methodology for accurate cross-language performance comparison.
