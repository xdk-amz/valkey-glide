# Backend Selection Update

## Summary

Updated the interactive session script to support both ZSTD and LZ4 compression backends with command-line argument selection.

## Changes Made

### 1. Updated `interactive_session.py`

**New Features:**
- Added command-line argument parsing with `argparse`
- Support for `zstd` (default) and `lz4` backends
- Dynamic backend configuration in `setup_session()`
- New helper function `create_client_with_backend()` for runtime backend switching
- Updated help text and configuration display to show current backend

**Key Changes:**
- Added `backend` parameter to `setup_session()` function
- Backend-specific compression level handling (LZ4 doesn't use levels)
- Updated console help text to include new backend function
- Proper argument validation and help message

### 2. Updated `run_interactive.sh`

**New Features:**
- Command-line argument parsing for backend selection
- Input validation with helpful error messages
- Backend information in startup messages

**Usage:**
```bash
# Default ZSTD backend
./run_interactive.sh

# Explicit backend selection
./run_interactive.sh zstd
./run_interactive.sh lz4

# Invalid backend shows help
./run_interactive.sh invalid
```

### 3. Updated `README.md`

**Documentation Updates:**
- Added backend selection examples to Quick Start
- Updated Key Features to mention both ZSTD and LZ4 backends
- Clear usage instructions for both backends

### 4. Added Test Script

**New File:** `test_backend_selection.py`
- Validates argument parsing works correctly
- Tests shell script validation
- Ensures help messages are properly displayed

## Usage Examples

### Command Line Usage

```bash
# Start with ZSTD (default)
./run_interactive.sh

# Start with LZ4
./run_interactive.sh lz4

# Direct Python usage
python3 interactive_session.py lz4
```

### Interactive Session Functions

```python
# Create client with different backend
lz4_client = create_client_with_backend('lz4')
zstd_client = create_client_with_backend('zstd')

# Create ZSTD client with specific level
high_compression_client = create_client_with_level(9)
```

## Backend Differences

### ZSTD
- Configurable compression levels (1-22)
- Better compression ratios
- Slightly slower compression/decompression
- Default level: 3

### LZ4
- Fixed compression algorithm (no levels)
- Faster compression/decompression
- Lower compression ratios
- Optimized for speed

## Backward Compatibility

- Default behavior unchanged (ZSTD with level 3)
- All existing functions work as before
- New functions are additive, not breaking changes
- Shell script works without arguments (defaults to ZSTD)

## Testing

The update has been tested for:
- ✅ Argument parsing and validation
- ✅ Shell script backend selection
- ✅ Help message display
- ✅ Backward compatibility
- ⚠️  Full functionality testing requires proper GLIDE environment

## Next Steps

To fully test the LZ4 backend functionality:
1. Set up the Python environment with `./setup_environment.sh`
2. Ensure Redis/Valkey server is running
3. Test both backends: `./run_interactive.sh lz4` and `./run_interactive.sh zstd`
4. Compare performance using the `compare_compression()` function
