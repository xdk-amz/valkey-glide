#!/bin/bash

# Script to run the comprehensive Go compression benchmark

echo "🚀 Running Go Compression Benchmark"
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

# Check if we're in the right directory
if [ ! -f "compression_benchmark.go" ]; then
    echo "❌ Error: compression_benchmark.go not found"
    echo "Please run this script from the go/benchmarks directory"
    exit 1
fi

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "❌ Error: Go is not installed or not in PATH"
    echo "Please install Go first: https://golang.org/doc/install"
    exit 1
fi

echo "✅ Go is available"

# Check if go.mod exists
if [ ! -f "go.mod" ]; then
    echo "❌ Error: go.mod not found"
    echo "Please ensure you're in the correct Go benchmarks directory"
    exit 1
fi

# Check Go dependencies
echo "📦 Checking Go dependencies..."
if ! go mod tidy; then
    echo "❌ Error: Failed to resolve Go dependencies"
    echo "Please check your go.mod file and network connection"
    exit 1
fi

echo "✅ Go dependencies are ready"

# Build the benchmark
echo "🔨 Building compression benchmark..."
if ! go build -o compression_benchmark compression_benchmark.go; then
    echo "❌ Error: Failed to build compression benchmark"
    echo "Please check the Go code for compilation errors"
    exit 1
fi

echo "✅ Benchmark built successfully"

# Run the benchmark
echo "🔨 Running comprehensive compression benchmark..."
echo "Running CompressionBenchmark..."

./compression_benchmark

# Clean up the binary
rm -f compression_benchmark

echo ""
echo "🎉 Benchmark completed!"
