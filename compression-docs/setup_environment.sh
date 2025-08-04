#!/bin/bash

echo "🚀 Setting up Python Environment for GLIDE Compression Testing"
echo "=" $(printf '=%.0s' {1..60})

# Check if we're in the right directory
if [ ! -d "../python" ]; then
    echo "❌ Error: python directory not found"
    echo "Please run this script from the compression-docs directory"
    exit 1
fi

# Navigate to python directory
cd ../python

# Check if virtual environment exists
if [ ! -d ".env" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .env
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install project dependencies
echo "📦 Installing GLIDE Python client..."
pip install -e .

# Install additional dependencies
echo "📦 Installing additional dependencies..."
pip install redis

# Verify installation
echo "✅ Verifying installation..."
python -c "import glide; print('GLIDE imported successfully')" 2>/dev/null && echo "✅ GLIDE client working" || echo "❌ GLIDE client has issues"
python -c "import redis; print('Redis imported successfully')" 2>/dev/null && echo "✅ Redis client working" || echo "❌ Redis client has issues"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To use the environment:"
echo "1. cd ../python"
echo "2. source .env/bin/activate"
echo "3. cd ../compression-docs"
echo "4. python3 basic_compression_test.py"
echo ""
echo "Or run the quick setup:"
echo "./run_interactive.sh"
