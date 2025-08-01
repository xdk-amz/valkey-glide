#!/bin/bash

# Script to run the simplified C# compression benchmark

echo "🚀 Running Simple C# Compression Benchmark"
echo "=" $(printf '=%.0s' {1..50})

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

# Check if .NET is installed
if ! command -v dotnet &> /dev/null; then
    echo "❌ Error: .NET is not installed or not in PATH"
    echo "Please install .NET first: https://dotnet.microsoft.com/download"
    exit 1
fi

echo "✅ .NET is available: $(dotnet --version)"

# Check if project file exists
if [ ! -f "SimpleCompressionBenchmark.csproj" ]; then
    echo "❌ Error: SimpleCompressionBenchmark.csproj not found"
    echo "Please ensure you're in the correct C# benchmarks directory"
    exit 1
fi

# Restore dependencies
echo "📦 Restoring .NET dependencies..."
if ! dotnet restore SimpleCompressionBenchmark.csproj --verbosity quiet; then
    echo "❌ Error: Failed to restore .NET dependencies"
    exit 1
fi

echo "✅ .NET dependencies are ready"

# Build and run the benchmark
echo "🔨 Building and running simple compression benchmark..."
dotnet run --project SimpleCompressionBenchmark.csproj -c Release

echo ""
echo "🎉 Simple benchmark completed!"
