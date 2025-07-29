// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Threading.Tasks;
using Glide;

/// <summary>
/// This example demonstrates how to use automatic compression with Valkey GLIDE.
/// It shows various compression configurations and use cases.
/// </summary>
public class CompressionExample
{
    /// <summary>
    /// Creates a GlideClient with compression configuration.
    /// </summary>
    private static async Task<GlideClient> CreateClientWithCompressionAsync(
        CompressionConfiguration compressionConfig = null,
        bool useCluster = false)
    {
        var addresses = new[] { new NodeAddress("localhost", 6379) };

        if (useCluster)
        {
            var clusterConfig = new GlideClusterClientConfiguration
            {
                Addresses = addresses,
                Compression = compressionConfig,
                RequestTimeout = 2000
            };
            return await GlideClusterClient.CreateAsync(clusterConfig);
        }
        else
        {
            var config = new GlideClientConfiguration
            {
                Addresses = addresses,
                Compression = compressionConfig,
                RequestTimeout = 2000
            };
            return await GlideClient.CreateAsync(config);
        }
    }

    /// <summary>
    /// Demonstrates basic compression usage with default settings.
    /// </summary>
    public static async Task BasicCompressionExampleAsync()
    {
        Console.WriteLine("=== Basic Compression Example ===");

        // Create compression configuration with defaults
        var compressionConfig = new CompressionConfiguration
        {
            Enabled = true,
            Backend = CompressionBackend.Zstd,
            // CompressionLevel defaults to 3
            // MinCompressionSize defaults to 64 bytes
        };

        using var client = await CreateClientWithCompressionAsync(compressionConfig);

        // Store some data that will be compressed
        var largeData = new
        {
            user_id = "12345",
            name = "John Doe",
            email = "john.doe@example.com",
            preferences = new
            {
                theme = "dark",
                language = "en",
                notifications = true
            },
            data = new string('x', 1000) // Large field to ensure compression
        };

        var jsonStr = JsonSerializer.Serialize(largeData);
        Console.WriteLine($"Original JSON size: {jsonStr.Length} bytes");

        // Set the data (will be automatically compressed)
        await client.SetAsync("user:12345", jsonStr);
        Console.WriteLine("Data stored with compression");

        // Get the data (will be automatically decompressed)
        var retrievedData = await client.GetAsync("user:12345");
        var retrievedJson = JsonSerializer.Deserialize<JsonElement>(retrievedData);

        Console.WriteLine($"Retrieved data matches: {jsonStr == retrievedData}");
        Console.WriteLine($"Retrieved user: {retrievedJson.GetProperty("name").GetString()}");
    }

    /// <summary>
    /// Demonstrates different compression configurations for various use cases.
    /// </summary>
    public static async Task CompressionConfigurationExamplesAsync()
    {
        Console.WriteLine("=== Compression Configuration Examples ===");

        // High-performance configuration (fast compression)
        var highPerformanceConfig = new CompressionConfiguration
        {
            Enabled = true,
            Backend = CompressionBackend.Zstd,
            CompressionLevel = 1,        // Fastest compression
            MinCompressionSize = 128,    // Skip smaller values
            MaxCompressionSize = 1024 * 1024  // 1MB limit
        };

        // High-compression configuration (better compression ratio)
        var highCompressionConfig = new CompressionConfiguration
        {
            Enabled = true,
            Backend = CompressionBackend.Zstd,
            CompressionLevel = 6,        // Better compression
            MinCompressionSize = 32,     // Compress more values
            MaxCompressionSize = null    // No size limit
        };

        // Balanced configuration (recommended for most use cases)
        var balancedConfig = new CompressionConfiguration
        {
            Enabled = true,
            Backend = CompressionBackend.Zstd,
            CompressionLevel = 3,        // Good balance
            MinCompressionSize = 64,     // Standard threshold
            MaxCompressionSize = 10 * 1024 * 1024  // 10MB limit
        };

        var configs = new Dictionary<string, CompressionConfiguration>
        {
            ["High Performance"] = highPerformanceConfig,
            ["High Compression"] = highCompressionConfig,
            ["Balanced"] = balancedConfig
        };

        var testData = string.Join("", System.Linq.Enumerable.Repeat("The quick brown fox jumps over the lazy dog. ", 100)); // ~4.3KB

        foreach (var (configName, config) in configs)
        {
            Console.WriteLine($"Testing {configName} configuration");

            using var client = await CreateClientWithCompressionAsync(config);
            var key = $"test:{configName.ToLower().Replace(" ", "_")}";

            // Measure compression performance
            var stopwatch = Stopwatch.StartNew();
            await client.SetAsync(key, testData);
            var setTime = stopwatch.ElapsedMilliseconds;

            stopwatch.Restart();
            var retrieved = await client.GetAsync(key);
            var getTime = stopwatch.ElapsedMilliseconds;

            Console.WriteLine($"  Set time: {setTime}ms, Get time: {getTime}ms");
            Console.WriteLine($"  Data integrity: {testData == retrieved}");
        }
    }

    /// <summary>
    /// Demonstrates compression with batch operations (pipelines and transactions).
    /// </summary>
    public static async Task BatchOperationsExampleAsync()
    {
        Console.WriteLine("=== Batch Operations with Compression ===");

        var compressionConfig = new CompressionConfiguration
        {
            Enabled = true,
            Backend = CompressionBackend.Zstd,
            MinCompressionSize = 32  // Lower threshold for demo
        };

        using var client = await CreateClientWithCompressionAsync(compressionConfig);

        // Pipeline example
        Console.WriteLine("Testing pipeline with compression");

        var pipelineData = new Dictionary<string, string>
        {
            ["user:1"] = JsonSerializer.Serialize(new { name = "Alice", data = new string('A', 500) }),
            ["user:2"] = JsonSerializer.Serialize(new { name = "Bob", data = new string('B', 500) }),
            ["user:3"] = JsonSerializer.Serialize(new { name = "Charlie", data = new string('C', 500) })
        };

        // Use pipeline to set multiple values (all will be compressed)
        var pipeline = new Pipeline();
        foreach (var (key, value) in pipelineData)
        {
            pipeline.Set(key, value);
        }
        pipeline.MGet(pipelineData.Keys.ToArray());
        var results = await client.ExecAsync(pipeline);

        Console.WriteLine($"Pipeline executed, got {results.Length} results");

        // The last result is from MGET - verify decompression worked
        var mgetResults = (string[])results[results.Length - 1];
        var index = 0;
        foreach (var (key, originalValue) in pipelineData)
        {
            var matches = originalValue == mgetResults[index];
            Console.WriteLine($"  {key}: {matches}");
            index++;
        }

        // Transaction example
        Console.WriteLine("Testing transaction with compression");

        var counterData0 = JsonSerializer.Serialize(new { count = 0, data = new string('x', 200) });
        var counterData1 = JsonSerializer.Serialize(new { count = 1, data = new string('x', 200) });

        var transaction = new Transaction();
        transaction.Set("counter:compressed", counterData0);
        transaction.Get("counter:compressed");
        transaction.Set("counter:compressed", counterData1);
        transaction.Get("counter:compressed");
        var txResults = await client.ExecAsync(transaction);

        Console.WriteLine($"Transaction executed, got {txResults.Length} results");

        // Verify the final counter value
        var finalData = JsonSerializer.Deserialize<JsonElement>(txResults[txResults.Length - 1].ToString());
        Console.WriteLine($"Final counter value: {finalData.GetProperty("count").GetInt32()}");
    }

    /// <summary>
    /// Demonstrates compatibility between compression-enabled and disabled clients.
    /// </summary>
    public static async Task MixedClientScenarioAsync()
    {
        Console.WriteLine("=== Mixed Client Scenario ===");

        // Client with compression enabled
        var compressionConfig = new CompressionConfiguration { Enabled = true };
        using var compressedClient = await CreateClientWithCompressionAsync(compressionConfig);

        // Client with compression disabled
        var noCompressionConfig = new CompressionConfiguration { Enabled = false };
        using var uncompressedClient = await CreateClientWithCompressionAsync(noCompressionConfig);

        var testData = string.Join("", System.Linq.Enumerable.Repeat("This is test data that will be compressed. ", 50));

        // Store data with compression-enabled client
        await compressedClient.SetAsync("mixed:test", testData);
        Console.WriteLine("Data stored with compression-enabled client");

        // Read with compression-enabled client (automatic decompression)
        var compressedRead = await compressedClient.GetAsync("mixed:test");
        Console.WriteLine($"Compression-enabled client read: {testData == compressedRead}");

        // Read with compression-disabled client (gets raw compressed data)
        var uncompressedRead = await uncompressedClient.GetAsync("mixed:test");
        Console.WriteLine($"Compression-disabled client read raw data size: {uncompressedRead?.Length ?? 0} bytes");
        Console.WriteLine($"Raw data is different from original: {testData != uncompressedRead}");

        // Store uncompressed data
        await uncompressedClient.SetAsync("mixed:uncompressed", testData);
        Console.WriteLine("Data stored with compression-disabled client");

        // Read uncompressed data with both clients
        var compressedReadUncomp = await compressedClient.GetAsync("mixed:uncompressed");
        var uncompressedReadUncomp = await uncompressedClient.GetAsync("mixed:uncompressed");

        var bothCorrect = testData == compressedReadUncomp && testData == uncompressedReadUncomp;
        Console.WriteLine($"Both clients read uncompressed data correctly: {bothCorrect}");
    }

    /// <summary>
    /// Compares performance with and without compression.
    /// </summary>
    public static async Task PerformanceComparisonAsync()
    {
        Console.WriteLine("=== Performance Comparison ===");

        // Test data of different types
        var testCases = new Dictionary<string, string>
        {
            ["Small JSON"] = JsonSerializer.Serialize(new { id = 1, name = "test" }),
            ["Large JSON"] = JsonSerializer.Serialize(new 
            { 
                id = 1, 
                data = new string('x', 2000), 
                metadata = new { created = "2024-01-01" } 
            }),
            ["Repetitive Text"] = string.Join("", System.Linq.Enumerable.Repeat("Hello World! ", 200)),
            ["Random-like Data"] = string.Join("", System.Linq.Enumerable.Repeat("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 40))
        };

        var configs = new Dictionary<string, CompressionConfiguration>
        {
            ["No Compression"] = new CompressionConfiguration { Enabled = false },
            ["With Compression"] = new CompressionConfiguration { Enabled = true, MinCompressionSize = 10 }
        };

        foreach (var (testName, testData) in testCases)
        {
            Console.WriteLine($"Testing: {testName} ({testData.Length} bytes)");

            foreach (var (configName, config) in configs)
            {
                using var client = await CreateClientWithCompressionAsync(config);
                var key = $"perf:{testName.ToLower().Replace(" ", "_")}";

                // Measure set performance
                var stopwatch = Stopwatch.StartNew();
                await client.SetAsync(key, testData);
                var setTime = stopwatch.ElapsedMilliseconds;

                // Measure get performance
                stopwatch.Restart();
                var retrieved = await client.GetAsync(key);
                var getTime = stopwatch.ElapsedMilliseconds;

                // Verify data integrity
                var dataMatches = testData == retrieved;

                Console.WriteLine($"  {configName}: SET {setTime}ms, GET {getTime}ms, Integrity: {dataMatches}");
            }

            Console.WriteLine();
        }
    }

    /// <summary>
    /// Demonstrates error handling with compression.
    /// </summary>
    public static async Task ErrorHandlingExampleAsync()
    {
        Console.WriteLine("=== Error Handling Example ===");

        try
        {
            // Try to create client with invalid configuration
            var invalidConfig = new CompressionConfiguration
            {
                Enabled = true,
                CompressionLevel = 100,  // Invalid level for ZSTD (max is 22)
            };

            using var client = await CreateClientWithCompressionAsync(invalidConfig);
        }
        catch (Exception e)
        {
            Console.WriteLine($"Expected configuration error: {e.GetType().Name}");
        }

        // Valid configuration with error handling
        var compressionConfig = new CompressionConfiguration { Enabled = true };
        using var validClient = await CreateClientWithCompressionAsync(compressionConfig);

        try
        {
            // Normal operation
            await validClient.SetAsync("error:test", "test data");
            var result = await validClient.GetAsync("error:test");
            Console.WriteLine($"Normal operation successful: {result}");

            // Compression errors are handled gracefully by the client
            // (fallback to uncompressed data with warning logs)
        }
        catch (Exception e)
        {
            Console.WriteLine($"Unexpected error: {e.Message}");
            throw;
        }
    }

    /// <summary>
    /// Demonstrates compression with cluster client.
    /// </summary>
    public static async Task ClusterCompressionExampleAsync()
    {
        Console.WriteLine("=== Cluster Compression Example ===");

        var compressionConfig = new CompressionConfiguration
        {
            Enabled = true,
            Backend = CompressionBackend.Zstd,
            MinCompressionSize = 32
        };

        try
        {
            // Note: Adjust the address for your cluster setup
            var addresses = new[] { new NodeAddress("localhost", 7000) };
            var clusterConfig = new GlideClusterClientConfiguration
            {
                Addresses = addresses,
                Compression = compressionConfig,
                RequestTimeout = 2000
            };

            using var clusterClient = await GlideClusterClient.CreateAsync(clusterConfig);

            // Test compression with cluster operations
            var clusterData = new Dictionary<string, string>
            {
                ["cluster:user:1"] = JsonSerializer.Serialize(new { name = "Alice", region = "us-east", data = new string('A', 300) }),
                ["cluster:user:2"] = JsonSerializer.Serialize(new { name = "Bob", region = "us-west", data = new string('B', 300) }),
                ["cluster:user:3"] = JsonSerializer.Serialize(new { name = "Charlie", region = "eu-west", data = new string('C', 300) })
            };

            // Set data across cluster (values will be compressed)
            foreach (var (key, value) in clusterData)
            {
                await clusterClient.SetAsync(key, value);
            }

            Console.WriteLine("Data stored across cluster with compression");

            // Retrieve data (values will be decompressed)
            var keys = clusterData.Keys.ToArray();
            var retrievedValues = await clusterClient.MGetAsync(keys);

            for (int i = 0; i < keys.Length; i++)
            {
                var key = keys[i];
                var original = clusterData[key];
                var retrieved = retrievedValues[i];
                var matches = original == retrieved;
                Console.WriteLine($"  {key}: {matches}");
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"Cluster example skipped (cluster not available): {e.Message}");
        }
    }

    /// <summary>
    /// Main method that runs all compression examples.
    /// </summary>
    public static async Task Main(string[] args)
    {
        Console.WriteLine("Starting Valkey GLIDE Compression Examples");
        Console.WriteLine(new string('=', 60));

        try
        {
            await BasicCompressionExampleAsync();
            await CompressionConfigurationExamplesAsync();
            await BatchOperationsExampleAsync();
            await MixedClientScenarioAsync();
            await PerformanceComparisonAsync();
            await ErrorHandlingExampleAsync();
            await ClusterCompressionExampleAsync();
        }
        catch (Exception e)
        {
            Console.WriteLine($"Example failed: {e.Message}");
            throw;
        }

        Console.WriteLine(new string('=', 60));
        Console.WriteLine("All compression examples completed successfully!");
    }
}
