#!/bin/bash

# Script to run the comprehensive Python compression benchmark

echo "🚀 Running Python Compression Benchmark"
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
if [ ! -f "compression_benchmark.py" ]; then
    echo "❌ Error: compression_benchmark.py not found"
    echo "Please run this script from the benchmarks/python directory"
    exit 1
fi

# Check if Python environment is set up
if [ ! -d "../../python/.env" ]; then
    echo "❌ Error: Python virtual environment not found"
    echo "Please set up the Python environment first:"
    echo "  cd ../../python"
    echo "  python -m venv .env"
    echo "  source .env/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate Python virtual environment
echo "🔧 Activating Python virtual environment..."
source ../../python/.env/bin/activate

# Check if required packages are installed
echo "📦 Checking Python dependencies..."
python -c "import glide; print('✅ GLIDE Python client is available')" 2>/dev/null || {
    echo "❌ Error: GLIDE Python client not found"
    echo "Please install the GLIDE Python client first:"
    echo "  cd ../../python"
    echo "  source .env/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
}

# Run the benchmark
echo "🔨 Running comprehensive compression benchmark..."
echo "Running CompressionBenchmark..."

python compression_benchmark.py

echo ""
echo "🎉 Benchmark completed!"
