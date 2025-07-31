#!/bin/bash

# Script to run the comprehensive Java compression benchmark

echo "🚀 Running Java Compression Benchmark"
echo "=" $(printf '=%.0s' {1..60})

# Check if Valkey/Redis is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo "❌ Error: Redis/Valkey server not running on localhost:6379"
    echo "Please start a Redis/Valkey server first:"
    echo "  redis-server"
    echo "  # or"
    echo "  valkey-server"
    exit 1
fi

echo "✅ Redis/Valkey server is running"

# Build and run using gradle
echo "🔨 Building and running comprehensive compression benchmark..."

# Temporarily change the main class to our benchmark
sed -i.bak "s/mainClass = 'glide.benchmarks.BenchmarkingApp'/mainClass = 'glide.benchmarks.CompressionBenchmark'/" benchmarks/build.gradle

# Run the benchmark
echo "Running CompressionBenchmark..."
./gradlew :benchmarks:run -q

# Restore the original main class
mv benchmarks/build.gradle.bak benchmarks/build.gradle

echo ""
echo "🎉 Benchmark completed!"
