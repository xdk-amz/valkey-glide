# Compression Integration Tests

This directory contains comprehensive integration tests for the automatic compression feature in Valkey Glide. The tests verify cross-language compatibility, backward compatibility, performance characteristics, and error handling.

## Test Structure

### 1. Cross-Language Compatibility Tests
- **Files**: `cross_language_compatibility_test.py`, `cross_language_compatibility_test.ts`
- **Purpose**: Verify that data compressed by one language binding can be decompressed by another
- **Coverage**:
  - Python ↔ Node.js data exchange
  - Consistent compression format across language bindings
  - Automated bidirectional compatibility testing

### 2. Backward Compatibility Tests
- **Files**: `backward_compatibility_test.py`, `backward_compatibility_test.ts`
- **Purpose**: Ensure compression feature doesn't break existing functionality
- **Coverage**:
  - Compression-enabled clients reading uncompressed data
  - Compression-disabled clients reading compressed data
  - Mixed client scenarios
  - Gradual migration from uncompressed to compressed
  - Data integrity across different configurations

### 3. Performance and Error Handling Tests
- **Files**: `performance_and_error_handling_test.py`, `performance_and_error_handling_test.ts`
- **Purpose**: Benchmark performance and verify robust error handling
- **Coverage**:
  - Compression/decompression latency overhead
  - Compression ratio effectiveness for different data types
  - Graceful fallback behavior
  - Configuration validation and error reporting
  - Memory usage patterns

## Prerequisites

### Server Setup
1. Start a Valkey or Redis server on `localhost:6379`:
   ```bash
   # Using Redis
   redis-server
   
   # Or using Valkey
   valkey-server
   ```

### Python Environment
1. Navigate to the Python client directory:
   ```bash
   cd python
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Node.js Environment
1. Navigate to the Node.js client directory:
   ```bash
   cd node
   ```

2. Install dependencies and build:
   ```bash
   npm install
   npm run build
   ```

## Running the Tests

### Quick Start - All Tests
Use the provided shell script to run all tests:
```bash
cd integration-tests/compression
chmod +x run_cross_language_tests.sh
./run_cross_language_tests.sh
```

### Individual Test Suites

#### Cross-Language Compatibility Tests
```bash
# Python version
cd python
python3 ../integration-tests/compression/cross_language_compatibility_test.py

# Node.js version
cd node
npx ts-node ../integration-tests/compression/cross_language_compatibility_test.ts
```

#### Backward Compatibility Tests
```bash
# Python version
cd python
python3 ../integration-tests/compression/backward_compatibility_test.py

# Node.js version
cd node
npx ts-node ../integration-tests/compression/backward_compatibility_test.ts
```

#### Performance and Error Handling Tests
```bash
# Python version
cd python
python3 ../integration-tests/compression/performance_and_error_handling_test.py

# Node.js version
cd node
npx ts-node ../integration-tests/compression/performance_and_error_handling_test.ts
```

## Test Data Types

The tests use various data types to ensure comprehensive coverage:

- **Small data**: Below compression threshold (< 32 bytes)
- **Medium data**: Good compression candidates (hundreds of bytes)
- **Large data**: High compression benefit (thousands of bytes)
- **JSON data**: Structured text data
- **Binary data**: Non-text binary patterns
- **Unicode text**: Multi-language text with special characters
- **Highly compressible**: Repetitive data (high compression ratio)
- **Poorly compressible**: Random data (low compression ratio)
- **Edge cases**: Empty data, single bytes

## Expected Results

### Cross-Language Compatibility
- ✅ Data compressed by Python should be readable by Node.js
- ✅ Data compressed by Node.js should be readable by Python
- ✅ Compression format should be consistent across languages
- ✅ Magic headers should be properly handled

### Backward Compatibility
- ✅ Compression-enabled clients should read uncompressed data correctly
- ✅ Compression-disabled clients should receive raw compressed bytes
- ✅ Mixed client scenarios should not cause data corruption
- ✅ Gradual migration should be seamless

### Performance Benchmarks
- ✅ Compression overhead should be reasonable (typically < 50% for SET/GET operations)
- ✅ Compression ratios should be effective:
  - Text data: 2-5x compression
  - JSON data: 3-8x compression
  - Repetitive data: 10-100x compression
  - Random data: ~1x (no compression benefit)

### Error Handling
- ✅ Invalid configurations should be rejected
- ✅ Compression failures should fall back gracefully
- ✅ Memory usage should be stable under load
- ✅ Configuration validation should provide clear error messages

## Troubleshooting

### Common Issues

1. **Server not running**:
   ```
   Error: Valkey/Redis server is not running on localhost:6379
   ```
   **Solution**: Start a Valkey or Redis server on port 6379

2. **Python dependencies missing**:
   ```
   ModuleNotFoundError: No module named 'glide'
   ```
   **Solution**: Install Python dependencies and ensure you're in the correct directory

3. **Node.js build not found**:
   ```
   Cannot find module './build-ts'
   ```
   **Solution**: Run `npm run build` in the node directory

4. **Permission denied on shell script**:
   ```
   Permission denied: ./run_cross_language_tests.sh
   ```
   **Solution**: Run `chmod +x run_cross_language_tests.sh`

### Test Failures

If tests fail, check:

1. **Server connectivity**: Ensure the server is accessible and responding
2. **Data integrity**: Look for data mismatch messages in the output
3. **Configuration errors**: Check for invalid compression settings
4. **Memory issues**: Monitor system resources during large data tests
5. **Network timeouts**: Increase timeout values if needed

### Performance Variations

Performance results may vary based on:
- System hardware (CPU, memory)
- Server load and configuration
- Network latency (even for localhost)
- Background processes

Typical performance characteristics:
- **Small data** (< 32 bytes): No compression, minimal overhead
- **Medium data** (32-1KB): 10-30% overhead, 2-5x compression
- **Large data** (> 1KB): 5-20% overhead, 3-10x compression

## Integration with CI/CD

These tests can be integrated into continuous integration pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Compression Integration Tests
  run: |
    # Start Redis server
    redis-server --daemonize yes
    
    # Run tests
    cd integration-tests/compression
    ./run_cross_language_tests.sh
```

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Include both Python and Node.js versions for consistency
3. Add appropriate error handling and cleanup
4. Update this README with new test descriptions
5. Ensure tests are deterministic and don't depend on external state

## Requirements Coverage

These integration tests fulfill the following requirements from the specification:

- **Requirement 4.2**: Cross-language compatibility verification
- **Requirement 8.1**: Backward compatibility with existing uncompressed data
- **Requirement 8.2**: Compression-disabled clients reading compressed data
- **Requirement 8.3**: Consistent compression format across language bindings
- **Requirement 8.5**: Gradual migration support
- **Requirement 2.3**: Graceful fallback behavior
- **Requirement 3.3**: Error handling for decompression failures
- **Requirement 5.3**: Configuration validation
- **Requirement 1.4**: Configuration error reporting
