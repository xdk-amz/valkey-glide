# Go Compression Benchmark

This directory contains a comprehensive compression benchmark for the GLIDE Go client, following the same test format and dataset as the Python and Java benchmarks.

## Overview

The Go compression benchmark tests:
1. Various realistic data types (JSON, logs, CSV, XML, etc.)
2. Different compression levels and their impact on TPS
3. Memory usage comparison between compressed and uncompressed
4. Throughput measurements for different data sizes
5. Compression effectiveness across different data patterns

## Files

- `compression_benchmark.go` - Main benchmark implementation
- `run_compression_benchmark.sh` - Shell script to run the benchmark
- `README_compression.md` - This documentation file

## Prerequisites

1. **Go**: Make sure Go is installed (version 1.22 or later)
2. **Redis/Valkey Server**: A running Redis or Valkey server on localhost:6379
3. **Dependencies**: The benchmark uses the same datasets as Java benchmarks

## Usage

### Quick Start

```bash
# Make sure you're in the go/benchmarks directory
cd go/benchmarks

# Run the benchmark using the shell script
./run_compression_benchmark.sh
```

### Manual Execution

```bash
# Build the benchmark
go build -o compression_benchmark compression_benchmark.go

# Run the benchmark
./compression_benchmark

# Clean up
rm compression_benchmark
```

## Benchmark Configuration

The benchmark uses the following configuration:
- **Warmup iterations**: 100
- **Benchmark iterations**: 1000  
- **TPS test duration**: 5000ms (5 seconds)
- **Compression level**: 1 (ZSTD) for TPS measurements
- **Min compression size**: 64 bytes

## Test Datasets

The benchmark uses standardized datasets from `../../java/benchmarks/data/`:

- **json_objects**: JSON data structures
- **app_logs**: Application log entries
- **csv_data**: CSV formatted data
- **xml_docs**: XML documents (uses `---` separator)
- **base64**: Base64 encoded data
- **repetitive**: Repetitive text patterns
- **random**: Random-like data
- **mixed_web**: Mixed web content (uses `---` separator)

## Benchmark Types

### 1. Compression Level Benchmark
Tests different ZSTD compression levels (1, 3, 6, 9, 15, 22) using JSON objects to measure:
- Original vs compressed size
- Compression ratio
- Throughput (TPS)

### 2. Data Type Compression Effectiveness
Tests all data types with ZSTD level 1 compression to measure:
- Compression ratio for different data patterns
- Memory savings percentage
- Throughput impact

### 3. Throughput Benchmark
Compares performance between compressed and uncompressed operations:
- SET/GET operations per second
- Performance impact percentage

### 4. Memory Efficiency Benchmark
Measures actual Redis memory usage:
- Uncompressed vs compressed memory consumption
- Memory savings percentage

## Sample Output

```
🚀 GLIDE Go Compression Benchmark
=============================================================
Warmup iterations: 100
Benchmark iterations: 1000
TPS test duration: 5000ms

📊 Loading standardized test datasets...
  json_objects : 100 entries,   45,234 total bytes, 452 avg bytes
  app_logs     : 150 entries,   67,890 total bytes, 452 avg bytes
  ...

🎚️ Compression Level Benchmark
--------------------------------------------------------------------------------
Level  Dataset      Original   Compressed Ratio    TPS
--------------------------------------------------------------------------------
1      json_objects     45,234     28,156  1.61   12,450
3      json_objects     45,234     25,789  1.75   11,890
...

📋 Data Type Compression Effectiveness
   Measures compression ratio and memory savings for different data types
--------------------------------------------------------------------------------
Dataset      Entries  Original   Redis Mem  Ratio    TPS      Savings
--------------------------------------------------------------------------------
json_objects     100    45,234     28,156   1.61   12,450     37.8%
app_logs         150    67,890     41,234   1.65   11,890     39.3%
...
```

## Implementation Details

### Compression Configuration
The benchmark uses the GLIDE Go client's compression configuration:

```go
config := config.NewCompressionConfig().
    WithEnabled(true).
    WithBackend(config.Zstd).
    WithCompressionLevel(level).
    WithMinCompressionSize(64)
```

### Client Setup
```go
clientConfig := config.NewClientConfiguration().
    WithAddress(&config.NodeAddress{Host: "localhost", Port: 6379}).
    WithCompression(compressionConfig)

client, err := glide.NewClient(clientConfig)
```

### Memory Usage Measurement
The benchmark uses Redis's `MEMORY USAGE` command to measure actual memory consumption:

```go
result, err := client.CustomCommand(ctx, []string{"MEMORY", "USAGE", key})
```

## Error Handling

The benchmark includes comprehensive error handling:
- Dataset loading failures fall back to generated data
- Memory usage measurement failures fall back to data length
- Client connection errors are properly reported
- Build and runtime errors are clearly displayed

## Troubleshooting

### Common Issues

1. **Redis/Valkey not running**:
   ```
   ❌ Error: Redis/Valkey server not running on localhost:6379
   ```
   Solution: Start Redis/Valkey server before running the benchmark

2. **Go not installed**:
   ```
   ❌ Error: Go is not installed or not in PATH
   ```
   Solution: Install Go from https://golang.org/doc/install

3. **Dataset files not found**:
   ```
   ⚠️ Failed to load json_objects.txt: file not found
   ```
   Solution: Ensure you're running from the correct directory and Java benchmark data exists

4. **Build failures**:
   ```
   ❌ Error: Failed to build compression benchmark
   ```
   Solution: Check Go version compatibility and dependencies

## Performance Notes

- The benchmark measures actual Redis memory usage, not just compressed data size
- TPS measurements include both SET and GET operations
- Warmup iterations ensure stable performance measurements
- Different data types show varying compression effectiveness
- Higher compression levels trade speed for better compression ratios

## Comparison with Other Languages

This Go benchmark produces comparable results to the Python and Java versions:
- Uses identical datasets and test methodology
- Measures the same metrics (TPS, compression ratio, memory usage)
- Follows the same output format for easy comparison
- Tests the same compression levels and configurations

The Go implementation typically shows:
- Similar compression ratios to other languages
- Competitive throughput performance
- Consistent memory usage patterns
- Reliable error handling and fallback behavior
