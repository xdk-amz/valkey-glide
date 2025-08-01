// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using System.Diagnostics;
using StackExchange.Redis;

namespace Valkey.Glide.SimpleCompressionBenchmark;

/// <summary>
/// Simplified C# compression benchmark using StackExchange.Redis
/// to demonstrate compression concepts without GLIDE dependencies.
/// </summary>
public class SimpleCompressionBenchmark
{
    private const string HOST = "localhost";
    private const int PORT = 6379;

    public static async Task Main(string[] args)
    {
        Console.WriteLine("🚀 Simple C# Compression Benchmark");
        Console.WriteLine(new string('=', 50));
        Console.WriteLine("Using StackExchange.Redis to demonstrate compression concepts");
        Console.WriteLine();

        try
        {
            var benchmark = new SimpleCompressionBenchmark();
            await benchmark.RunBenchmark();
            Console.WriteLine("\n🎉 Benchmark completed successfully!");
        }
        catch (Exception e)
        {
            Console.WriteLine($"\n❌ Error during benchmark: {e.GetType().Name}: {e.Message}");
            Environment.Exit(1);
        }
    }

    private async Task RunBenchmark()
    {
        // Connect to Redis
        var connection = ConnectionMultiplexer.Connect($"{HOST}:{PORT}");
        var db = connection.GetDatabase();

        Console.WriteLine("✅ Connected to Redis server");
        Console.WriteLine();

        // Load test datasets
        var datasets = await LoadTestDatasets();

        // Run benchmarks
        await BenchmarkDataSizes(db, datasets);
        await BenchmarkDataTypes(db, datasets);
        await CompareMemoryUsage(db, datasets);

        connection.Close();
    }

    private async Task<Dictionary<string, List<string>>> LoadTestDatasets()
    {
        Console.WriteLine("📊 Loading test datasets...");

        var datasets = new Dictionary<string, List<string>>();
        var dataDir = "../data";

        // Try to load from files, fallback to generated data
        datasets["json_objects"] = await LoadDatasetFromFile(Path.Combine(dataDir, "json_objects.txt"), false);
        datasets["app_logs"] = await LoadDatasetFromFile(Path.Combine(dataDir, "app_logs.txt"), false);
        datasets["repetitive"] = await LoadDatasetFromFile(Path.Combine(dataDir, "repetitive_text.txt"), false);
        datasets["random"] = await LoadDatasetFromFile(Path.Combine(dataDir, "random_data.txt"), false);

        // Print dataset info
        foreach (var kvp in datasets)
        {
            var totalSize = kvp.Value.Sum(v => v.Length);
            var avgSize = kvp.Value.Count > 0 ? totalSize / kvp.Value.Count : 0;
            Console.WriteLine($"  {kvp.Key,-12}: {kvp.Value.Count,3} entries, {totalSize,8:N0} total bytes, {avgSize,5:N0} avg bytes");
        }
        Console.WriteLine();

        return datasets;
    }

    private async Task<List<string>> LoadDatasetFromFile(string filename, bool useSeparator)
    {
        try
        {
            var content = await File.ReadAllTextAsync(filename);
            var entries = new List<string>();

            if (useSeparator)
            {
                var parts = content.Split(new[] { "---" }, StringSplitOptions.RemoveEmptyEntries);
                entries.AddRange(parts.Select(part => part.Trim()).Where(part => !string.IsNullOrEmpty(part)));
            }
            else
            {
                var lines = content.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
                entries.AddRange(lines.Select(line => line.Trim()).Where(line => !string.IsNullOrEmpty(line)));
            }

            return entries;
        }
        catch
        {
            // Generate fallback data
            var fallback = new List<string>();
            var baseName = Path.GetFileNameWithoutExtension(filename);
            
            for (int i = 0; i < 10; i++)
            {
                fallback.Add($"Generated {baseName} data entry {i} - " + new string('x', 50 + i * 10));
            }
            return fallback;
        }
    }

    private async Task BenchmarkDataSizes(IDatabase db, Dictionary<string, List<string>> datasets)
    {
        Console.WriteLine("📏 Data Size Impact on Redis Memory");
        Console.WriteLine(new string('-', 60));
        Console.WriteLine($"{"Size",-8} {"Data",-15} {"Redis Memory",-12} {"Overhead",-10}");
        Console.WriteLine(new string('-', 60));

        var sizes = new[] { 10, 50, 100, 500, 1000, 5000 };

        foreach (var size in sizes)
        {
            var data = new string('x', size);
            var key = $"size_test_{size}";
            
            await db.StringSetAsync(key, data);
            var memory = await GetMemoryUsage(db, key);
            var overhead = memory - size;

            Console.WriteLine($"{size,-8} {"x".Repeat(Math.Min(15, size)),-15} {memory,-12:N0} {overhead,-10:N0}");
        }
        Console.WriteLine();
    }

    private async Task BenchmarkDataTypes(IDatabase db, Dictionary<string, List<string>> datasets)
    {
        Console.WriteLine("🧪 Data Type Memory Usage Analysis");
        Console.WriteLine(new string('-', 70));
        Console.WriteLine($"{"Dataset",-12} {"Entries",-8} {"Avg Size",-10} {"Avg Memory",-12} {"Overhead %",-10}");
        Console.WriteLine(new string('-', 70));

        foreach (var kvp in datasets)
        {
            var totalMemory = 0L;
            var totalSize = 0;

            // Test a sample of entries
            var sampleSize = Math.Min(5, kvp.Value.Count);
            for (int i = 0; i < sampleSize; i++)
            {
                var key = $"{kvp.Key}_test_{i}";
                var data = kvp.Value[i];
                
                await db.StringSetAsync(key, data);
                var memory = await GetMemoryUsage(db, key);
                
                totalMemory += memory;
                totalSize += data.Length;
            }

            var avgSize = totalSize / sampleSize;
            var avgMemory = totalMemory / sampleSize;
            var overheadPercent = avgSize > 0 ? ((double)(avgMemory - avgSize) / avgSize) * 100 : 0;

            Console.WriteLine($"{kvp.Key,-12} {kvp.Value.Count,-8} {avgSize,-10:N0} {avgMemory,-12:N0} {overheadPercent,-10:F1}%");
        }
        Console.WriteLine();
    }

    private async Task CompareMemoryUsage(IDatabase db, Dictionary<string, List<string>> datasets)
    {
        Console.WriteLine("💾 Simulated Compression Benefits");
        Console.WriteLine("   (Shows potential memory savings with compression)");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Dataset",-12} {"Original",-10} {"Simulated",-10} {"Ratio",-8} {"Savings",-10}");
        Console.WriteLine(new string('-', 80));

        foreach (var kvp in datasets)
        {
            var originalSize = kvp.Value.Sum(v => v.Length);
            var simulatedRatio = GetSimulatedCompressionRatio(kvp.Key);
            var compressedSize = (long)(originalSize / simulatedRatio);
            var savings = ((double)(originalSize - compressedSize) / originalSize) * 100;

            Console.WriteLine($"{kvp.Key,-12} {originalSize,-10:N0} {compressedSize,-10:N0} {simulatedRatio,-8:F2} {savings,-10:F1}%");
        }
        Console.WriteLine();
    }

    private double GetSimulatedCompressionRatio(string datasetName)
    {
        return datasetName switch
        {
            "json_objects" => 2.5,
            "app_logs" => 2.8,
            "repetitive" => 8.0,
            "random" => 1.1,
            _ => 2.0
        };
    }

    private async Task<long> GetMemoryUsage(IDatabase db, string key)
    {
        try
        {
            var result = await db.ExecuteAsync("MEMORY", "USAGE", key);
            return (long)result;
        }
        catch
        {
            // Fallback: estimate based on key + value + overhead
            var value = await db.StringGetAsync(key);
            return value.HasValue ? key.Length + value.ToString().Length + 50 : 0;
        }
    }
}

// Extension method for string repetition
public static class StringExtensions
{
    public static string Repeat(this string input, int count)
    {
        if (string.IsNullOrEmpty(input) || count <= 0)
            return string.Empty;
        
        return string.Concat(Enumerable.Repeat(input, count));
    }
}
