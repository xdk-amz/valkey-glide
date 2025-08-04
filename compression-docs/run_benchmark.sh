#!/bin/bash

echo "🚀 Running Compression Benchmarks"
echo "=" $(printf '=%.0s' {1..40})

# Check if virtual environment exists
if [ ! -d "../python/.env" ]; then
    echo "❌ Python virtual environment not found"
    echo "Please run ./setup_environment.sh first"
    exit 1
fi

# Check if Redis is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo "❌ Redis/Valkey server not running on localhost:6379"
    echo "Please start a Redis/Valkey server first:"
    echo "  redis-server"
    echo "  # or"
    echo "  valkey-server"
    exit 1
fi

echo "✅ Redis/Valkey server is running"

# Activate virtual environment
echo "🔌 Activating Python environment..."
cd ../python
source .env/bin/activate
cd ../compression-docs

# Create results directory
mkdir -p results

echo ""
echo "📊 Running basic compression test..."
python3 basic_compression_test.py

echo ""
echo "📊 Running comprehensive benchmark..."
python3 comprehensive_benchmark.py

echo ""
echo "📊 Running detailed compression benchmark..."
python3 compression_benchmark.py

echo ""
echo "🎉 All benchmarks completed!"
echo "📁 Results saved in the results/ directory"
