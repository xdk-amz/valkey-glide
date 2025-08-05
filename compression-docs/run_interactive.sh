#!/bin/bash

# Parse command line arguments
BACKEND=${1:-zstd}

# Validate backend argument
if [[ "$BACKEND" != "zstd" && "$BACKEND" != "lz4" ]]; then
    echo "❌ Invalid backend: $BACKEND"
    echo "Usage: $0 [backend]"
    echo "  backend: zstd (default) or lz4"
    exit 1
fi

echo "🎮 Starting Interactive Compression Session ($BACKEND backend)"
echo "=" $(printf '=%.0s' {1..50})

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
echo "🔧 Using $BACKEND compression backend"

# Activate virtual environment and run
echo "🔌 Activating Python environment..."
cd ../python
source .env/bin/activate
cd ../compression-docs

echo "🚀 Starting interactive session with $BACKEND backend..."
../.env/bin/python3 interactive_session.py "$BACKEND"
