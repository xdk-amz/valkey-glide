# Compression Benchmark Data

This folder contains standardized datasets for compression benchmarking across all GLIDE language bindings.

## Dataset Files

### `json_objects.txt`
- **Purpose**: Realistic JSON API responses, user profiles, product data, and order objects
- **Format**: One JSON object per line
- **Size Range**: 100-5000 bytes per object
- **Compression Expected**: Good (structured data with repeated keys)

### `app_logs.txt`
- **Purpose**: Application log entries with timestamps, levels, and messages
- **Format**: One log entry per line
- **Size Range**: 50-200 bytes per entry
- **Compression Expected**: Excellent (repetitive patterns)

### `csv_data.txt`
- **Purpose**: Tabular employee data in CSV format
- **Format**: CSV with headers, one record per line
- **Size Range**: 40-100 bytes per record
- **Compression Expected**: Good (structured, repetitive headers)

### `xml_docs.txt`
- **Purpose**: Various XML documents (products, orders, configurations)
- **Format**: XML documents separated by `---`
- **Size Range**: 200-1000 bytes per document
- **Compression Expected**: Good (verbose markup, repeated tags)

### `repetitive_text.txt`
- **Purpose**: Highly repetitive content (error messages, batch processing logs)
- **Format**: One entry per line
- **Size Range**: 50-500 bytes per entry
- **Compression Expected**: Excellent (high repetition)

### `base64_data.txt`
- **Purpose**: Base64 encoded strings (simulating binary data)
- **Format**: One base64 string per line
- **Size Range**: 50-200 bytes per entry
- **Compression Expected**: Poor (random-like characteristics)

### `random_data.txt`
- **Purpose**: Random character sequences (worst case for compression)
- **Format**: One random string per line
- **Size Range**: 100-1000 bytes per entry
- **Compression Expected**: Poor (no patterns)

### `mixed_web.txt`
- **Purpose**: Web content (HTML, CSS, JavaScript, Markdown)
- **Format**: Different content types separated by `---`
- **Size Range**: 200-2000 bytes per section
- **Compression Expected**: Good (repeated HTML/CSS patterns)

## Usage

These files are designed to be used by compression benchmarks across all GLIDE language bindings:

1. **Java**: `CompressionBenchmark.java` loads these files
2. **Python**: Can use the same files for consistent benchmarking
3. **Future languages**: Will use the same standardized dataset

## Benefits

- **Consistency**: Same data across all language benchmarks
- **Realism**: Data represents real-world usage patterns
- **Variety**: Different compression characteristics for comprehensive testing
- **Maintainability**: Single source of truth for benchmark data
- **Comparability**: Results can be compared across language implementations

## File Format

Each file contains multiple entries:
- **Line-based files**: One entry per line (JSON, logs, CSV, base64, random)
- **Section-based files**: Entries separated by `---` (XML, mixed web content)

This standardization ensures that all language bindings test compression with identical data, making performance comparisons meaningful and accurate.
