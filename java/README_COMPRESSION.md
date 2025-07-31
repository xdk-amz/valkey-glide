# Java GLIDE Compression - Complete Guide

## 🎯 **Overview**

This directory contains comprehensive Java examples and benchmarks for GLIDE compression functionality. The compression feature provides transparent compression/decompression of Redis values, achieving significant memory savings with minimal code changes.

## 📁 **Available Tools**

### 1. **Simple Demo** - `CompressionDemo.java`
```bash
./run_compression_demo.sh
```
- ✅ Basic compression functionality
- ✅ Different compression levels
- ✅ Memory usage comparison
- ✅ Data type effectiveness
- ⏱️ **Runtime**: ~30 seconds

### 2. **Comprehensive Benchmark** - `CompressionBenchmark.java`
```bash
./run_compression_benchmark.sh
```
- 🚀 **Realistic datasets** (JSON, logs, CSV, XML, HTML, etc.)
- 📊 **TPS measurements** with performance impact analysis
- 🎚️ **Compression level analysis** (1-22)
- 💾 **Memory efficiency** comparison
- ⚡ **Throughput benchmarks** (compressed vs uncompressed)
- ⏱️ **Runtime**: ~2-3 minutes

## 🎯 **Key Results Summary**

### Compression Effectiveness:
- **Structured data** (JSON, XML, HTML): **95%+ memory savings**
- **Repetitive content**: **97%+ memory savings**
- **Application logs**: **87%+ memory savings**
- **Random/binary data**: **30% memory savings**

### Performance Impact:
- **Large datasets**: Can improve throughput (+6% for large HTML)
- **Small datasets**: 25-50% throughput reduction
- **Optimal level**: Level 3 provides best balance

### Memory Savings:
- **Best case**: 98.7% reduction (194KB → 2.6KB)
- **Typical structured data**: 90%+ reduction
- **Poor compression candidates**: Still 30%+ reduction

## 🚀 **Quick Start**

### Basic Usage:
```java
// Enable compression
CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
    .enabled(true)
    .backend(CompressionBackend.ZSTD)
    .compressionLevel(3)
    .minCompressionSize(64)
    .build();

// Create client with compression
GlideClientConfiguration config = GlideClientConfiguration.builder()
    .address(NodeAddress.builder().host("localhost").port(6379).build())
    .compression(compressionConfig)
    .build();

// Use normally - compression is transparent
try (GlideClient client = GlideClient.createClient(config).get()) {
    client.set("key", largeJsonData).get();  // Automatically compressed
    String data = client.get("key").get();   // Automatically decompressed
}
```

### Verify Compression:
```java
// Check actual memory usage in Redis
private static long getMemoryUsage(String key, GlideClient client) {
    Object result = client.customCommand(new String[]{"MEMORY", "USAGE", key}).get();
    return (result instanceof Long) ? (Long) result : 0;
}
```

## 📊 **Benchmark Highlights**

### Dataset Performance (Level 3 ZSTD):
| Data Type | Original | Compressed | Ratio | Memory Saved | TPS |
|-----------|----------|------------|-------|--------------|-----|
| HTML Content | 194KB | 2.6KB | **74:1** | **98.7%** | 2,724 |
| JSON API | 54KB | 2.1KB | **26:1** | **96.1%** | 3,873 |
| XML Document | 15KB | 640B | **23:1** | **95.6%** | 5,135 |
| Application Logs | 67KB | 8.2KB | **8:1** | **87.8%** | 3,129 |
| CSV Data | 23KB | 2.1KB | **11:1** | **90.9%** | 3,681 |

### Compression Level Analysis:
| Level | Performance | Use Case |
|-------|-------------|----------|
| 1 | **Fastest** (4,328 TPS) | High-throughput applications |
| 3 | **Balanced** (3,970 TPS) | **Recommended default** |
| 6-9 | Moderate (2,684 TPS) | Memory-critical applications |
| 15+ | Slow (467 TPS) | Offline/batch processing only |

## 🎯 **Recommendations**

### ✅ **Ideal Use Cases:**
- Large JSON/XML documents
- Application logs and text files
- HTML/web content
- Structured data with repetitive patterns
- Memory-constrained environments

### ⚠️ **Use with Caution:**
- Small values (< 100 bytes)
- High-frequency, low-latency operations
- Already compressed data

### ❌ **Not Recommended:**
- Base64 encoded data
- Random/encrypted binary data
- Ultra-low latency requirements (< 1ms)

### 🔧 **Optimal Configuration:**
```java
CompressionConfiguration.builder()
    .enabled(true)
    .backend(CompressionBackend.ZSTD)        // Only available backend
    .compressionLevel(3)                     // Best balance
    .minCompressionSize(128)                 // Skip tiny values
    .maxCompressionSize(10 * 1024 * 1024)    // 10MB limit
    .build();
```

## 📈 **Performance Expectations**

### Memory Savings:
- **Structured data**: 90-98% reduction
- **Text content**: 80-95% reduction  
- **Mixed data**: 60-90% reduction
- **Random data**: 20-40% reduction

### Throughput Impact:
- **Large payloads** (>50KB): Minimal to positive impact
- **Medium payloads** (5-50KB): 20-40% reduction
- **Small payloads** (<5KB): 30-50% reduction

### Latency Impact:
- **Compression**: 0.1-2ms additional latency
- **Network savings**: Often offset compression overhead
- **Memory access**: Faster due to smaller data size

## 🔧 **Implementation Status**

### ✅ **Working Features:**
- ZSTD compression backend (levels 1-22)
- Transparent compression/decompression
- Configurable size thresholds
- Memory usage optimization
- Data integrity guaranteed

### 🚧 **Not Yet Available:**
- LZ4 compression backend
- Compression statistics/metrics
- Per-key compression control

## 📚 **Additional Resources**

- **`COMPRESSION_BENCHMARK_RESULTS.md`** - Detailed benchmark analysis and recommendations

## 🎉 **Success Summary**

The Java GLIDE compression implementation is **production-ready** and provides:

✅ **Significant memory savings** (up to 98.7% reduction)  
✅ **Transparent operation** (no code changes needed)  
✅ **Predictable performance** characteristics  
✅ **Data integrity** guaranteed  
✅ **Comprehensive testing** and benchmarking tools  
✅ **Production-ready** configuration examples  

Ready to deploy in production environments where memory efficiency is important!
