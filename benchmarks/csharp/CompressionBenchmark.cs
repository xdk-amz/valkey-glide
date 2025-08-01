// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace Valkey.Glide.CompressionBenchmark;

/// <summary>
/// Comprehensive C# benchmark for GLIDE client compression performance.
/// 
/// This benchmark tests:
/// 1. Various realistic data types (JSON, logs, CSV, XML, etc.)
/// 2. Different compression levels and their impact on TPS
/// 3. Memory usage comparison between compressed and uncompressed
/// 4. Throughput measurements for different data sizes
/// 5. Compression effectiveness across different data patterns
/// </summary>
public class CompressionBenchmark
{
    private const string HOST = "localhost";
    private const ushort PORT = 6379;
    private const int WARMUP_ITERATIONS = 100;
    private const int BENCHMARK_ITERATIONS = 1000;
    private const int TPS_TEST_DURATION_MS = 5000; // 5 seconds

    /// <summary>
    /// Holds the results of a benchmark run
    /// </summary>
    public class BenchmarkResult
    {
        public double TPS { get; set; }
        public long CompressedSize { get; set; }
        public double CompressionRatio { get; set; }
    }

    public static async Task Main(string[] args)
    {
        Console.WriteLine("🚀 GLIDE C# Compression Benchmark");
        Console.WriteLine(new string('=', 61));
        Console.WriteLine($"Warmup iterations: {WARMUP_ITERATIONS}");
        Console.WriteLine($"Benchmark iterations: {BENCHMARK_ITERATIONS}");
        Console.WriteLine($"TPS test duration: {TPS_TEST_DURATION_MS}ms");
        Console.WriteLine();

        try
        {
            var benchmark = new CompressionBenchmark();

            // Load standardized test datasets
            var datasets = await benchmark.LoadTestDatasets();

            // Run comprehensive benchmarks
            await benchmark.BenchmarkCompressionLevels(datasets);
            await benchmark.BenchmarkDataTypes(datasets);
            await benchmark.BenchmarkThroughput(datasets);
            await benchmark.BenchmarkMemoryEfficiency(datasets);

            Console.WriteLine("\n🎉 Benchmark completed successfully!");
        }
        catch (Exception e)
        {
            Console.WriteLine($"\n❌ Error during benchmark: {e.GetType().Name}: {e.Message}");
            Environment.Exit(1);
        }
    }

    /// <summary>
    /// Load standardized test datasets from files
    /// </summary>
    private async Task<Dictionary<string, List<string>>> LoadTestDatasets()
    {
        Console.WriteLine("📊 Loading standardized test datasets...");

        var datasets = new Dictionary<string, List<string>>();
        var dataDir = "../data";

        // Load datasets from standardized files
        datasets["json_objects"] = await LoadDatasetFromFile(Path.Combine(dataDir, "json_objects.txt"), false);
        datasets["app_logs"] = await LoadDatasetFromFile(Path.Combine(dataDir, "app_logs.txt"), false);
        datasets["csv_data"] = await LoadDatasetFromFile(Path.Combine(dataDir, "csv_data.txt"), false);
        datasets["xml_docs"] = await LoadDatasetFromFile(Path.Combine(dataDir, "xml_docs.txt"), true); // XML uses --- separator
        datasets["base64"] = await LoadDatasetFromFile(Path.Combine(dataDir, "base64_data.txt"), false);
        datasets["repetitive"] = await LoadDatasetFromFile(Path.Combine(dataDir, "repetitive_text.txt"), false);
        datasets["random"] = await LoadDatasetFromFile(Path.Combine(dataDir, "random_data.txt"), false);
        datasets["mixed_web"] = await LoadDatasetFromFile(Path.Combine(dataDir, "mixed_web.txt"), true); // Mixed web uses --- separator

        // Print dataset info
        foreach (var kvp in datasets)
        {
            var totalSize = kvp.Value.Sum(v => v.Length);
            var avgSize = kvp.Value.Count > 0 ? totalSize / kvp.Value.Count : 0;
            Console.WriteLine($"  {kvp.Key,-12}: {kvp.Value.Count,3:N0} entries, {totalSize,8:N0} total bytes, {avgSize,5:N0} avg bytes");
        }
        Console.WriteLine();

        return datasets;
    }

    /// <summary>
    /// Load dataset from a file
    /// </summary>
    private async Task<List<string>> LoadDatasetFromFile(string filename, bool useSeparator)
    {
        var entries = new List<string>();

        try
        {
            var content = await File.ReadAllTextAsync(filename);

            if (useSeparator)
            {
                // Split by --- separator for XML and mixed web content
                var parts = content.Split(new[] { "---" }, StringSplitOptions.RemoveEmptyEntries);
                entries.AddRange(parts.Select(part => part.Trim()).Where(part => !string.IsNullOrEmpty(part)));
            }
            else
            {
                // Split by lines for other formats
                var lines = content.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
                entries.AddRange(lines.Select(line => line.Trim()).Where(line => !string.IsNullOrEmpty(line)));
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"⚠️ Failed to load {filename}: {e.GetType().Name} - {e.Message}");
            Console.WriteLine("   Using fallback generated data for this dataset");
            entries.AddRange(GenerateFallbackData(Path.GetFileName(filename)));
        }

        return entries;
    }

    /// <summary>
    /// Generate fallback data if file loading fails
    /// </summary>
    private List<string> GenerateFallbackData(string filename)
    {
        var fallback = new List<string>();
        for (int i = 0; i < 10; i++)
        {
            fallback.Add($"Fallback data entry {i} for {filename}");
        }
        return fallback;
    }

    /// <summary>
    /// Benchmark different compression levels
    /// </summary>
    private async Task BenchmarkCompressionLevels(Dictionary<string, List<string>> datasets)
    {
        Console.WriteLine("🎚️ Compression Level Benchmark");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Level",-6} {"Dataset",-12} {"Original",-10} {"Compressed",-10} {"Ratio",-8} {"TPS",-8}");
        Console.WriteLine(new string('-', 80));

        var levels = new[] { 1, 3, 6, 9, 15, 22 };
        var testDataset = datasets["json_objects"]; // Use JSON for level testing

        foreach (var level in levels)
        {
            var result = await BenchmarkConfiguration(
                CreateCompressionConfig(CompressionBackend.Zstd, level, 64),
                $"json_objects_level_{level}", testDataset);

            var originalSize = testDataset.Sum(data => data.Length);

            Console.WriteLine($"{level,-6} {"json_objects",-12} {originalSize,10:N0} {result.CompressedSize,10:N0} {result.CompressionRatio,-8:F2} {result.TPS,8:F0}");
        }

        Console.WriteLine();
    }

    /// <summary>
    /// Benchmark different data types
    /// </summary>
    private async Task BenchmarkDataTypes(Dictionary<string, List<string>> datasets)
    {
        Console.WriteLine("📋 Data Type Compression Effectiveness");
        Console.WriteLine("   Measures compression ratio and memory savings for different data types");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Dataset",-12} {"Entries",-8} {"Original",-10} {"Redis Mem",-10} {"Ratio",-8} {"TPS",-8} {"Savings",-10}");
        Console.WriteLine(new string('-', 80));

        var config = CreateCompressionConfig(CompressionBackend.Zstd, 1, 64);

        foreach (var kvp in datasets)
        {
            var result = await BenchmarkConfiguration(config, kvp.Key, kvp.Value);
            var originalSize = kvp.Value.Sum(entry => entry.Length);
            var savings = originalSize > 0 ? ((double)(originalSize - result.CompressedSize) / originalSize) * 100 : 0;

            Console.WriteLine($"{kvp.Key,-12} {kvp.Value.Count,8:N0} {originalSize,10:N0} {result.CompressedSize,10:N0} {result.CompressionRatio,-8:F2} {result.TPS,8:F0} {savings,9:F1}%");
        }

        Console.WriteLine();
    }

    /// <summary>
    /// Benchmark throughput with different configurations
    /// </summary>
    private async Task BenchmarkThroughput(Dictionary<string, List<string>> datasets)
    {
        Console.WriteLine("⚡ Throughput Benchmark (Operations/Second)");
        Console.WriteLine("   Measures performance impact of compression on SET/GET operations");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Dataset",-12} {"Uncompressed",-12} {"Compressed",-12} {"Perf Impact",-12}");
        Console.WriteLine(new string('-', 80));

        var compressedConfig = CreateCompressionConfig(CompressionBackend.Zstd, 1, 64);

        foreach (var kvp in datasets)
        {
            // Benchmark uncompressed
            var uncompressed = await BenchmarkConfiguration(null, $"{kvp.Key}_uncomp", kvp.Value);

            // Benchmark compressed
            var compressed = await BenchmarkConfiguration(compressedConfig, $"{kvp.Key}_comp", kvp.Value);

            var difference = uncompressed.TPS > 0 ? ((compressed.TPS - uncompressed.TPS) / uncompressed.TPS) * 100 : 0;

            Console.WriteLine($"{kvp.Key,-12} {uncompressed.TPS,12:F0} {compressed.TPS,12:F0} {difference,+11:F1}%");
        }

        Console.WriteLine();
    }

    /// <summary>
    /// Benchmark memory efficiency
    /// </summary>
    private async Task BenchmarkMemoryEfficiency(Dictionary<string, List<string>> datasets)
    {
        Console.WriteLine("💾 Memory Efficiency Benchmark");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Dataset",-12} {"Entries",-8} {"Original",-10} {"Uncomp Mem",-10} {"Comp Mem",-10} {"Mem Saved",-10}");
        Console.WriteLine(new string('-', 80));

        var compressedConfig = CreateCompressionConfig(CompressionBackend.Zstd, 1, 64);

        foreach (var kvp in datasets)
        {
            // Test uncompressed memory usage
            var uncompressedMemory = await MeasureMemoryUsage(null, $"{kvp.Key}_mem_uncomp", kvp.Value);

            // Test compressed memory usage
            var compressedMemory = await MeasureMemoryUsage(compressedConfig, $"{kvp.Key}_mem_comp", kvp.Value);

            var originalSize = kvp.Value.Sum(entry => entry.Length);
            var memorySaved = uncompressedMemory > 0 ? ((double)(uncompressedMemory - compressedMemory) / uncompressedMemory) * 100 : 0;

            Console.WriteLine($"{kvp.Key,-12} {kvp.Value.Count,8:N0} {originalSize,10:N0} {uncompressedMemory,10:N0} {compressedMemory,10:N0} {memorySaved,9:F1}%");
        }

        Console.WriteLine();
    }

    /// <summary>
    /// Benchmark a specific configuration
    /// </summary>
    private async Task<BenchmarkResult> BenchmarkConfiguration(CompressionConfiguration? compressionConfig,
        string keyPrefix, List<string> dataList)
    {
        // Create client configuration
        var configBuilder = new StandaloneClientConfigurationBuilder()
            .WithAddress(HOST, PORT);

        if (compressionConfig.HasValue)
        {
            configBuilder.WithCompression(compressionConfig.Value);
        }

        using var client = await GlideClient.CreateClient(configBuilder.Build());

        // Warmup - use different entries for each warmup iteration
        for (int i = 0; i < WARMUP_ITERATIONS; i++)
        {
            var data = dataList[i % dataList.Count];
            var key = $"{keyPrefix}_warmup_{i}";
            await client.StringSetAsync(key, data);
        }

        // Measure TPS
        var stopwatch = Stopwatch.StartNew();
        var operations = 0;

        while (stopwatch.ElapsedMilliseconds < TPS_TEST_DURATION_MS)
        {
            var data = dataList[operations % dataList.Count];
            var key = $"{keyPrefix}_tps_{operations}";

            await client.StringSetAsync(key, data);
            await client.StringGetAsync(key);

            operations += 2; // SET + GET
        }

        stopwatch.Stop();
        var tps = operations / (stopwatch.ElapsedMilliseconds / 1000.0);

        // Measure compression across all entries
        long totalCompressedSize = 0;
        var originalSize = 0;

        for (int i = 0; i < dataList.Count; i++)
        {
            var testKey = $"{keyPrefix}_size_test_{i}";
            await client.StringSetAsync(testKey, dataList[i]);

            var memUsage = await GetMemoryUsage(testKey, client);
            totalCompressedSize += memUsage;
            originalSize += dataList[i].Length;
        }

        // Handle case where memory usage couldn't be measured
        if (totalCompressedSize == 0)
        {
            totalCompressedSize = originalSize; // Fallback to original size
        }

        // Calculate compression ratio
        var compressionRatio = compressionConfig.HasValue && totalCompressedSize > 0
            ? (double)originalSize / totalCompressedSize
            : 1.0; // No compression applied

        return new BenchmarkResult
        {
            TPS = tps,
            CompressedSize = totalCompressedSize,
            CompressionRatio = compressionRatio
        };
    }

    /// <summary>
    /// Measure memory usage for a configuration
    /// </summary>
    private async Task<long> MeasureMemoryUsage(CompressionConfiguration? compressionConfig,
        string keyPrefix, List<string> dataList)
    {
        // Create client configuration
        var configBuilder = new StandaloneClientConfigurationBuilder()
            .WithAddress(HOST, PORT);

        if (compressionConfig.HasValue)
        {
            configBuilder.WithCompression(compressionConfig.Value);
        }

        using var client = await GlideClient.CreateClient(configBuilder.Build());

        long totalMemory = 0;

        for (int i = 0; i < dataList.Count; i++)
        {
            var key = $"{keyPrefix}_{i}";
            await client.StringSetAsync(key, dataList[i]);
            totalMemory += await GetMemoryUsage(key, client);
        }

        return totalMemory;
    }

    /// <summary>
    /// Create compression configuration
    /// </summary>
    private CompressionConfiguration CreateCompressionConfig(CompressionBackend backend, uint level, uint minSize)
    {
        return new CompressionConfiguration(
            enabled: true,
            backend: backend,
            compressionLevel: level,
            minCompressionSize: minSize
        );
    }

    /// <summary>
    /// Get memory usage for a key
    /// </summary>
    private async Task<long> GetMemoryUsage(string key, BaseClient client)
    {
        try
        {
            var result = await client.CustomCommandAsync(new[] { "MEMORY", "USAGE", key });
            if (result.IsNull)
                return 0;

            // Try to parse the result as a long
            if (long.TryParse(result.ToString(), out var memoryUsage))
                return memoryUsage;

            return 0;
        }
        catch
        {
            return 0;
        }
    }
}
