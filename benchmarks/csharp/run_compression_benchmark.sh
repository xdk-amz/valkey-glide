#!/bin/bash

# Script to run the comprehensive C# compression benchmark

echo "🚀 Running C# Compression Benchmark"
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
if [ ! -f "CompressionBenchmark.cs" ]; then
    echo "❌ Error: CompressionBenchmark.cs not found"
    echo "Please run this script from the benchmarks/csharp directory"
    exit 1
fi

# Check if .NET is installed
if ! command -v dotnet &> /dev/null; then
    echo "❌ Error: .NET is not installed or not in PATH"
    echo "Please install .NET first: https://dotnet.microsoft.com/download"
    exit 1
fi

echo "✅ .NET is available"

# Check if project file exists
if [ ! -f "CompressionBenchmark.csproj" ]; then
    echo "❌ Error: CompressionBenchmark.csproj not found"
    echo "Please ensure you're in the correct C# benchmarks directory"
    exit 1
fi

# Restore dependencies
echo "📦 Restoring .NET dependencies..."
if ! dotnet restore CompressionBenchmark.csproj; then
    echo "❌ Error: Failed to restore .NET dependencies"
    echo "Please check your project file and network connection"
    exit 1
fi

echo "✅ .NET dependencies are ready"

# Build the benchmark
echo "🔨 Building compression benchmark..."
if ! dotnet build CompressionBenchmark.csproj -c Release; then
    echo "❌ Error: Failed to build compression benchmark"
    echo "Please check the C# code for compilation errors"
    exit 1
fi

echo "✅ Benchmark built successfully"

# Run the benchmark
echo "🔨 Running comprehensive compression benchmark..."
echo "Running CompressionBenchmark..."

dotnet run --project CompressionBenchmark.csproj -c Release

echo ""
echo "🎉 Benchmark completed!"
