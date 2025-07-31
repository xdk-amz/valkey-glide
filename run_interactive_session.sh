#!/bin/bash

echo "🎮 Starting Interactive Compression Session"
echo "=" $(printf '=%.0s' {1..40})

# Check if virtual environment exists
if [ ! -d "python/.env" ]; then
    echo "❌ Python virtual environment not found"
    echo "Please run ./setup_python_env.sh first"
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

# Activate virtual environment and run
echo "🔌 Activating Python environment..."
cd python
source .env/bin/activate
cd ..

echo "🚀 Starting interactive session..."
python3 interactive_compression_session.py
