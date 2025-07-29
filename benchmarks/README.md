# Benchmarks

[`install_and_test.sh`](./install_and_test.sh) is the benchmark script we use to check performance. run `install_and_test.sh -h` to get the full list of available flags.

The results of the benchmark runs will be written into .csv files in the `./results` folder.

## Python Compression Benchmarks

The Python client includes specialized compression benchmarks:

- **`python/compression_benchmark.py`** - Basic compression vs no-compression performance comparison
- **`python/comprehensive_compression_benchmark.py`** - Detailed analysis of different compression levels and configurations  
- **`python/compression_demo.py`** - Interactive demonstration of compression features

### Running Compression Benchmarks

```bash
# Basic compression benchmark
python/.env/bin/python benchmarks/python/compression_benchmark.py --minimal --dataSize 2000

# Comprehensive compression analysis
python/.env/bin/python benchmarks/python/comprehensive_compression_benchmark.py

# Interactive compression demo
python/.env/bin/python benchmarks/python/compression_demo.py
```

See [COMPRESSION_IMPLEMENTATION.md](../COMPRESSION_IMPLEMENTATION.md) for detailed results and analysis.

If while running benchmarks your redis-server is killed every time the program runs the 4000 data-size benchmark, it might be because you don't have enough available storage on your machine.
To solve this issue, you have two options -

1. Allocate more storage to your'e machine. for me the case was allocating from 500 gb to 1000 gb.
2. Go to benchmarks/install_and_test.sh and change the "dataSize="100 4000"" to a data-size that your machine can handle. try for example dataSize="100 1000".
