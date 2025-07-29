#!/bin/bash

# Cross-language compression compatibility test runner
# This script runs comprehensive tests to verify that data compressed by one
# language binding can be decompressed by another language binding.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Cross-Language Compression Compatibility Tests ==="
echo "Project root: $PROJECT_ROOT"
echo "Test directory: $SCRIPT_DIR"

# Check if Valkey/Redis server is running
check_server() {
    echo "Checking if Valkey/Redis server is running..."
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "Error: Valkey/Redis server is not running on localhost:6379"
        echo "Please start a Valkey/Redis server before running these tests"
        exit 1
    fi
    echo "✓ Server is running"
}

# Build Node.js client
build_nodejs() {
    echo "Building Node.js client..."
    cd "$PROJECT_ROOT/node"
    if [ ! -d "build-ts" ]; then
        npm run build
    fi
    echo "✓ Node.js client built"
}

# Install Python dependencies
setup_python() {
    echo "Setting up Python environment..."
    cd "$PROJECT_ROOT/python"
    if [ ! -f "requirements.txt" ]; then
        echo "Warning: requirements.txt not found, skipping Python setup"
        return
    fi
    
    # Check if virtual environment exists, create if not
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    echo "✓ Python environment ready"
}

# Run Python cross-language tests
run_python_tests() {
    echo "Running Python cross-language tests..."
    cd "$PROJECT_ROOT/python"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    python3 "$SCRIPT_DIR/cross_language_compatibility_test.py"
    local python_result=$?
    
    if [ $python_result -eq 0 ]; then
        echo "✓ Python cross-language tests passed"
    else
        echo "✗ Python cross-language tests failed"
    fi
    
    return $python_result
}

# Run Node.js cross-language tests
run_nodejs_tests() {
    echo "Running Node.js cross-language tests..."
    cd "$PROJECT_ROOT/node"
    
    npx ts-node "$SCRIPT_DIR/cross_language_compatibility_test.ts"
    local nodejs_result=$?
    
    if [ $nodejs_result -eq 0 ]; then
        echo "✓ Node.js cross-language tests passed"
    else
        echo "✗ Node.js cross-language tests failed"
    fi
    
    return $nodejs_result
}

# Run automated cross-language compatibility tests
run_automated_tests() {
    echo "Running automated cross-language compatibility tests..."
    
    # Create a test script that coordinates between languages
    local test_script="$SCRIPT_DIR/automated_cross_test.py"
    
    cat > "$test_script" << 'EOF'
#!/usr/bin/env python3
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time

# Add the Python client to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../python"))

from glide import GlideClient
from glide.config import (
    CompressionBackend,
    CompressionConfiguration,
    GlideClientConfiguration,
    NodeAddress,
)

async def test_bidirectional_compatibility():
    """Test bidirectional compatibility between Python and Node.js."""
    print("Testing bidirectional compression compatibility...")
    
    # Test data
    test_data = {
        "text_data": b"Hello, compression world!" * 50,
        "json_data": json.dumps({"test": "data", "numbers": list(range(100))}).encode(),
        "binary_data": bytes(range(256)) * 5,
    }
    
    # Python client configuration
    config = GlideClientConfiguration(
        addresses=[NodeAddress("127.0.0.1", 6379)],
        compression=CompressionConfiguration(
            enabled=True,
            backend=CompressionBackend.ZSTD,
            compression_level=3,
            min_compression_size=32,
        )
    )
    
    python_client = await GlideClient.create(config)
    
    try:
        # Store data with Python client
        python_keys = []
        for name, data in test_data.items():
            key = f"py_to_js:{name}"
            await python_client.set(key, data)
            python_keys.append(key)
            print(f"  Python stored: {key} ({len(data)} bytes)")
        
        # Create Node.js script to read Python data and store its own
        nodejs_script = '''
const { GlideClient, CompressionBackend } = require('./build-ts');

async function testCompatibility() {
    const client = await GlideClient.createClient({
        addresses: [{ host: '127.0.0.1', port: 6379 }],
        compression: {
            enabled: true,
            backend: CompressionBackend.ZSTD,
            compressionLevel: 3,
            minCompressionSize: 32,
        }
    });
    
    const testData = {
        "text_data": Buffer.from("Hello, compression world!".repeat(50)),
        "json_data": Buffer.from(JSON.stringify({"test": "data", "numbers": Array.from({length: 100}, (_, i) => i)})),
        "binary_data": Buffer.from(Array.from({length: 1280}, (_, i) => i % 256)),
    };
    
    try {
        // Read Python data
        const pythonKeys = ["py_to_js:text_data", "py_to_js:json_data", "py_to_js:binary_data"];
        const results = {};
        
        for (const key of pythonKeys) {
            const value = await client.get(key);
            if (value) {
                results[key] = Array.from(value);
            }
        }
        
        // Store Node.js data
        const nodeKeys = [];
        for (const [name, data] of Object.entries(testData)) {
            const key = `js_to_py:${name}`;
            await client.set(key, data);
            nodeKeys.push(key);
        }
        
        console.log(JSON.stringify({ pythonData: results, nodeKeys }));
    } finally {
        client.close();
    }
}

testCompatibility().catch(console.error);
'''
        
        # Write and run Node.js script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(nodejs_script)
            nodejs_script_path = f.name
        
        try:
            result = subprocess.run(
                ['node', nodejs_script_path],
                cwd='../../node',
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Node.js script failed: {result.stderr}")
                return False
            
            # Parse Node.js results
            nodejs_results = json.loads(result.stdout)
            
            # Verify Python data was read correctly by Node.js
            success_count = 0
            for name, expected_data in test_data.items():
                key = f"py_to_js:{name}"
                if key in nodejs_results["pythonData"]:
                    received_data = bytes(nodejs_results["pythonData"][key])
                    if received_data == expected_data:
                        success_count += 1
                        print(f"  ✓ Node.js correctly read Python data: {key}")
                    else:
                        print(f"  ✗ Node.js data mismatch for: {key}")
                else:
                    print(f"  ✗ Node.js could not read: {key}")
            
            # Read Node.js data with Python client
            for name, expected_data in test_data.items():
                key = f"js_to_py:{name}"
                received_data = await python_client.get(key)
                if received_data == expected_data:
                    success_count += 1
                    print(f"  ✓ Python correctly read Node.js data: {key}")
                else:
                    print(f"  ✗ Python data mismatch for: {key}")
            
            total_tests = len(test_data) * 2  # Both directions
            print(f"Bidirectional compatibility: {success_count}/{total_tests} tests passed")
            return success_count == total_tests
            
        finally:
            os.unlink(nodejs_script_path)
            
    finally:
        await python_client.close()

async def main():
    try:
        success = await test_bidirectional_compatibility()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    chmod +x "$test_script"
    
    cd "$PROJECT_ROOT/python"
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    python3 "$test_script"
    local result=$?
    
    rm -f "$test_script"
    return $result
}

# Main execution
main() {
    local overall_result=0
    
    echo "Starting cross-language compression compatibility test suite..."
    echo
    
    # Setup
    check_server
    build_nodejs
    setup_python
    
    echo
    echo "=== Running Tests ==="
    
    # Run Python tests
    echo
    if run_python_tests; then
        echo "✓ Python tests completed successfully"
    else
        echo "✗ Python tests failed"
        overall_result=1
    fi
    
    # Run Node.js tests
    echo
    if run_nodejs_tests; then
        echo "✓ Node.js tests completed successfully"
    else
        echo "✗ Node.js tests failed"
        overall_result=1
    fi
    
    # Run automated bidirectional tests
    echo
    if run_automated_tests; then
        echo "✓ Automated cross-language tests completed successfully"
    else
        echo "✗ Automated cross-language tests failed"
        overall_result=1
    fi
    
    echo
    echo "=== Test Summary ==="
    if [ $overall_result -eq 0 ]; then
        echo "✓ All cross-language compression compatibility tests passed!"
    else
        echo "✗ Some cross-language compression compatibility tests failed"
    fi
    
    return $overall_result
}

# Run main function
main "$@"
exit $?
