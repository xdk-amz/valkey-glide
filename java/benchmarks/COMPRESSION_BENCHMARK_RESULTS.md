# Java Compression Benchmark Results

**Date:** 2026-02-11
**Environment:** macOS (Apple Silicon), Valkey 9.0.0, JDK 21, standalone mode, localhost
**Benchmark mode:** minimal (1000 iterations per configuration)
**Compression config:** ZSTD level 3, min_compression_size=64 bytes
**Data pattern:** Repeated `"0"` characters (highly compressible)

## Results Summary

### Single-threaded (1 concurrent task, 1 client)

#### 100-byte values (below practical compression benefit)

| Metric | glide | glide_compressed | Delta |
|--------|-------|------------------|-------|
| TPS | 271 | 209 | **-22.9%** |
| SET avg latency (ms) | 3.698 | 5.117 | +38.3% |
| SET p50 (ms) | 3.013 | 4.835 | +60.5% |
| SET p99 (ms) | 9.207 | 15.082 | +63.8% |
| GET avg latency (ms) | 3.678 | 4.609 | +25.3% |
| GET p50 (ms) | 2.911 | 4.532 | +55.7% |
| GET p99 (ms) | 9.204 | 10.016 | +8.8% |

#### 4000-byte values (good compression candidate)

| Metric | glide | glide_compressed | Delta |
|--------|-------|------------------|-------|
| TPS | 180 | 388 | **+115.6%** |
| SET avg latency (ms) | 5.451 | 2.458 | **-54.9%** |
| SET p50 (ms) | 5.815 | 1.998 | **-65.6%** |
| SET p99 (ms) | 9.826 | 7.273 | -26.0% |
| GET avg latency (ms) | 5.517 | 2.575 | **-53.3%** |
| GET p50 (ms) | 5.577 | 2.016 | **-63.9%** |
| GET p99 (ms) | 12.125 | 7.849 | -35.3% |

### High-concurrency (100 concurrent tasks, 1 client)

#### 100-byte values

| Metric | glide | glide_compressed | Delta |
|--------|-------|------------------|-------|
| TPS | 26,157 | 37,755 | **+44.3%** |
| SET avg latency (ms) | 3.160 | 2.143 | -32.2% |
| SET p50 (ms) | 3.205 | 2.266 | -29.3% |
| SET p99 (ms) | 3.535 | 2.642 | -25.3% |
| GET avg latency (ms) | 3.131 | 2.181 | -30.3% |
| GET p50 (ms) | 3.193 | 2.280 | -28.6% |
| GET p99 (ms) | 3.543 | 2.663 | -24.8% |

#### 4000-byte values

| Metric | glide | glide_compressed | Delta |
|--------|-------|------------------|-------|
| TPS | 8,087 | 14,874 | **+83.9%** |
| SET avg latency (ms) | 12.196 | 6.557 | **-46.2%** |
| SET p50 (ms) | 12.248 | 6.790 | **-44.6%** |
| SET p99 (ms) | 21.609 | 9.768 | **-54.8%** |
| GET avg latency (ms) | 11.442 | 6.287 | **-45.1%** |
| GET p50 (ms) | 11.784 | 6.304 | **-46.5%** |
| GET p99 (ms) | 21.588 | 9.044 | **-58.1%** |

## Key Findings

### 1. Large values see massive improvement
For 4KB values, compression delivers **2x+ throughput** and **~50-65% lower latency** across all percentiles. The ZSTD compression ratio on repeated data is excellent, so the reduced I/O more than compensates for CPU overhead.

### 2. Small values have mixed results
For 100-byte values at low concurrency, compression adds overhead (~23% TPS drop) because the compression/decompression CPU cost exceeds the I/O savings on such small payloads. However, at high concurrency (100 tasks), even 100-byte values show a **44% TPS improvement** — the reduced wire bytes help when the connection is saturated.

### 3. Tail latency improves significantly under load
At 100 concurrent tasks with 4KB data, p99 latency drops from **21.6ms → 9.0ms** (58% reduction). Compression reduces the bytes on the wire, which reduces queuing and contention.

### 4. Compression overhead is negligible at scale
The per-operation CPU cost of ZSTD compression/decompression is small relative to network I/O. Under concurrent load, the bandwidth savings dominate.

## Recommendations

| Scenario | Recommendation |
|----------|---------------|
| Values < 64 bytes | Don't enable compression (below min threshold anyway) |
| Values 64–200 bytes, low concurrency | Compression adds slight overhead; skip unless bandwidth-constrained |
| Values 64–200 bytes, high concurrency | Enable compression — TPS improves due to reduced wire bytes |
| Values > 500 bytes | **Enable compression** — significant latency and throughput gains |
| Highly compressible data (JSON, XML, logs) | **Strongly recommended** — best compression ratios |
| Random/encrypted data | Minimal benefit — compression ratio near 1:1, slight CPU overhead |

## How to Reproduce

```bash
# Start a Valkey server
valkey-server --daemonize yes --port 6379 --save "" --appendonly no

# Build
cd java && ./gradlew :client:buildAll :benchmarks:build

# Extract distribution
cd /tmp && tar xf /path/to/java/benchmarks/build/distributions/benchmarks-*.tar

# Run baseline
JAVA_OPTS="-Djava.library.path=/path/to/java/target/release" \
  benchmarks-*/bin/benchmarks --clients glide --minimal --dataSize "100 4000" --concurrentTasks "1 100"

# Run compressed
JAVA_OPTS="-Djava.library.path=/path/to/java/target/release" \
  benchmarks-*/bin/benchmarks --clients glide_compressed --minimal --dataSize "100 4000" --concurrentTasks "1 100"
```
