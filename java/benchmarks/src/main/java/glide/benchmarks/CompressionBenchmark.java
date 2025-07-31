/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.benchmarks;

import glide.api.GlideClient;
import glide.api.models.configuration.CompressionBackend;
import glide.api.models.configuration.CompressionConfiguration;
import glide.api.models.configuration.GlideClientConfiguration;
import glide.api.models.configuration.NodeAddress;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.Random;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

/**
 * Comprehensive Java benchmark for GLIDE client compression performance.
 * 
 * This benchmark tests:
 * 1. Various realistic data types (JSON, logs, CSV, XML, etc.)
 * 2. Different compression levels and their impact on TPS
 * 3. Memory usage comparison between compressed and uncompressed
 * 4. Throughput measurements for different data sizes
 * 5. Compression effectiveness across different data patterns
 */
public class CompressionBenchmark {
    
    private static final String HOST = "localhost";
    private static final int PORT = 6379;
    private static final Random RANDOM = new Random(42); // Fixed seed for reproducible results
    
    // Benchmark configuration
    private static final int WARMUP_ITERATIONS = 100;
    private static final int BENCHMARK_ITERATIONS = 1000;
    private static final int TPS_TEST_DURATION_MS = 5000; // 5 seconds
    
    public static void main(String[] args) {
        System.out.println("🚀 GLIDE Java Compression Benchmark");
        System.out.println("=" + "=".repeat(60));
        System.out.println("Warmup iterations: " + WARMUP_ITERATIONS);
        System.out.println("Benchmark iterations: " + BENCHMARK_ITERATIONS);
        System.out.println("TPS test duration: " + TPS_TEST_DURATION_MS + "ms");
        System.out.println();
        
        try {
            // Load standardized test datasets
            Map<String, List<String>> datasets = loadTestDatasets();
            
            // Run comprehensive benchmarks
            benchmarkCompressionLevels(datasets);
            benchmarkDataTypes(datasets);
            benchmarkThroughput(datasets);
            benchmarkMemoryEfficiency(datasets);
            
            System.out.println("\n🎉 Benchmark completed successfully!");
            
        } catch (Exception e) {
            System.err.println("\n❌ Error during benchmark: " + e.getClass().getSimpleName() + ": " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Load standardized test datasets from files
     */
    private static Map<String, List<String>> loadTestDatasets() {
        System.out.println("📊 Loading standardized test datasets...");
        
        Map<String, List<String>> datasets = new HashMap<>();
        
        // Load datasets from standardized files
        datasets.put("json_objects", loadDatasetFromFile("json_objects.txt", false));
        datasets.put("app_logs", loadDatasetFromFile("app_logs.txt", false));
        datasets.put("csv_data", loadDatasetFromFile("csv_data.txt", false));
        datasets.put("xml_docs", loadDatasetFromFile("xml_docs.txt", true)); // XML uses --- separator
        datasets.put("base64", loadDatasetFromFile("base64_data.txt", false));
        datasets.put("repetitive", loadDatasetFromFile("repetitive_text.txt", false));
        datasets.put("random", loadDatasetFromFile("random_data.txt", false));
        datasets.put("mixed_web", loadDatasetFromFile("mixed_web.txt", true)); // Mixed web uses --- separator
        
        // Print dataset info
        for (Map.Entry<String, List<String>> entry : datasets.entrySet()) {
            List<String> values = entry.getValue();
            int totalSize = values.stream().mapToInt(String::length).sum();
            int avgSize = values.size() > 0 ? totalSize / values.size() : 0;
            System.out.printf("  %-12s: %3d entries, %,8d total bytes, %,5d avg bytes%n", 
                entry.getKey(), values.size(), totalSize, avgSize);
        }
        System.out.println();
        
        return datasets;
    }
    
    /**
     * Load dataset from a file
     */
    private static List<String> loadDatasetFromFile(String filename, boolean useSeparator) {
        List<String> entries = new ArrayList<>();
        String dataDir = "data/";
        
        try {
            java.nio.file.Path filePath = java.nio.file.Paths.get(dataDir + filename);
            if (!java.nio.file.Files.exists(filePath)) {
                throw new java.io.FileNotFoundException("File does not exist: " + filePath.toAbsolutePath());
            }
            String content = java.nio.file.Files.readString(filePath);
            
            if (useSeparator) {
                // Split by --- separator for XML and mixed web content
                String[] parts = content.split("---");
                for (String part : parts) {
                    String trimmed = part.trim();
                    if (!trimmed.isEmpty()) {
                        entries.add(trimmed);
                    }
                }
            } else {
                // Split by lines for other formats
                String[] lines = content.split("\n");
                for (String line : lines) {
                    String trimmed = line.trim();
                    if (!trimmed.isEmpty()) {
                        entries.add(trimmed);
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("⚠️ Failed to load " + filename + ": " + e.getClass().getSimpleName() + " - " + e.getMessage());
            System.err.println("   Attempted path: " + dataDir + filename);
            System.err.println("   Using fallback generated data for this dataset");
            // Fallback to generated data if file loading fails
            return generateFallbackData(filename);
        }
        
        return entries;
    }
    
    /**
     * Generate fallback data if file loading fails
     */
    private static List<String> generateFallbackData(String filename) {
        List<String> fallback = new ArrayList<>();
        
        // Simple fallback data generation
        for (int i = 0; i < 10; i++) {
            fallback.add(String.format("Fallback data entry %d for %s", i, filename));
        }
        
        return fallback;
    }
    
    /**
     * Benchmark different compression levels
     */
    private static void benchmarkCompressionLevels(Map<String, List<String>> datasets) throws ExecutionException, InterruptedException {
        System.out.println("🎚️ Compression Level Benchmark");
        System.out.println("-".repeat(80));
        System.out.printf("%-6s %-12s %-10s %-10s %-8s %-8s%n", 
            "Level", "Dataset", "Original", "Compressed", "Ratio", "TPS");
        System.out.println("-".repeat(80));
        
        int[] levels = {1, 3, 6, 9, 15, 22};
        List<String> testDataset = datasets.get("json_objects"); // Use JSON for level testing
        
        for (int level : levels) {
            BenchmarkResult result = benchmarkConfiguration(
                createCompressionConfig(CompressionBackend.ZSTD, level, 64),
                "json_objects", testDataset
            );
            
            int originalSize = testDataset.stream().mapToInt(String::length).sum();
            System.out.printf("%-6d %-12s %,10d %,10d %-8.2f %,8.0f%n",
                level, "json_objects", 
                originalSize, result.compressedSize,
                result.compressionRatio, result.tps);
        }
        System.out.println();
    }
    
    /**
     * Benchmark different data types
     */
    private static void benchmarkDataTypes(Map<String, List<String>> datasets) throws ExecutionException, InterruptedException {
        System.out.println("📋 Data Type Compression Effectiveness");
        System.out.println("   Measures compression ratio and memory savings for different data types");
        System.out.println("-".repeat(80));
        System.out.printf("%-12s %-8s %-10s %-10s %-8s %-8s %-10s%n", 
            "Dataset", "Entries", "Original", "Redis Mem", "Ratio", "TPS", "Savings");
        System.out.println("-".repeat(80));
        
        CompressionConfiguration config = createCompressionConfig(CompressionBackend.ZSTD, 3, 64);
        
        for (Map.Entry<String, List<String>> entry : datasets.entrySet()) {
            String datasetName = entry.getKey();
            List<String> data = entry.getValue();
            
            BenchmarkResult result = benchmarkConfiguration(config, datasetName, data);
            int originalSize = data.stream().mapToInt(String::length).sum();
            double savings = ((double)(originalSize - result.compressedSize) / originalSize) * 100;
            
            System.out.printf("%-12s %,8d %,10d %,10d %-8.2f %,8.0f %9.1f%%%n",
                datasetName, data.size(), originalSize, result.compressedSize,
                result.compressionRatio, result.tps, savings);
        }
        System.out.println();
    }
    
    /**
     * Benchmark throughput with different configurations
     */
    private static void benchmarkThroughput(Map<String, List<String>> datasets) throws ExecutionException, InterruptedException {
        System.out.println("⚡ Throughput Benchmark (Operations/Second)");
        System.out.println("   Measures performance impact of compression on SET/GET operations");
        System.out.println("-".repeat(80));
        System.out.printf("%-12s %-12s %-12s %-12s%n", 
            "Dataset", "Uncompressed", "Compressed", "Perf Impact");
        System.out.println("-".repeat(80));
        
        CompressionConfiguration compressedConfig = createCompressionConfig(CompressionBackend.ZSTD, 3, 64);
        
        for (Map.Entry<String, List<String>> entry : datasets.entrySet()) {
            String datasetName = entry.getKey();
            List<String> data = entry.getValue();
            
            // Benchmark uncompressed
            BenchmarkResult uncompressed = benchmarkConfiguration(null, datasetName + "_uncomp", data);
            
            // Benchmark compressed
            BenchmarkResult compressed = benchmarkConfiguration(compressedConfig, datasetName + "_comp", data);
            
            double difference = ((compressed.tps - uncompressed.tps) / uncompressed.tps) * 100;
            

            
            System.out.printf("%-12s %,12.0f %,12.0f %+11.1f%%%n",
                datasetName, uncompressed.tps, compressed.tps, difference);
        }
        System.out.println();
    }
    
    /**
     * Benchmark memory efficiency
     */
    private static void benchmarkMemoryEfficiency(Map<String, List<String>> datasets) throws ExecutionException, InterruptedException {
        System.out.println("💾 Memory Efficiency Benchmark");
        System.out.println("-".repeat(80));
        System.out.printf("%-12s %-8s %-10s %-10s %-10s %-10s%n", 
            "Dataset", "Entries", "Original", "Uncomp Mem", "Comp Mem", "Mem Saved");
        System.out.println("-".repeat(80));
        
        CompressionConfiguration compressedConfig = createCompressionConfig(CompressionBackend.ZSTD, 3, 64);
        
        for (Map.Entry<String, List<String>> entry : datasets.entrySet()) {
            String datasetName = entry.getKey();
            List<String> data = entry.getValue();
            
            // Test uncompressed memory usage
            long uncompressedMemory = measureMemoryUsage(null, datasetName + "_mem_uncomp", data);
            
            // Test compressed memory usage
            long compressedMemory = measureMemoryUsage(compressedConfig, datasetName + "_mem_comp", data);
            
            int originalSize = data.stream().mapToInt(String::length).sum();
            double memorySaved = ((double)(uncompressedMemory - compressedMemory) / uncompressedMemory) * 100;
            
            System.out.printf("%-12s %,8d %,10d %,10d %,10d %9.1f%%%n",
                datasetName, data.size(), originalSize, uncompressedMemory, compressedMemory, memorySaved);
        }
        System.out.println();
    }
    
    /**
     * Benchmark a specific configuration
     */
    private static BenchmarkResult benchmarkConfiguration(CompressionConfiguration compressionConfig, 
                                                         String keyPrefix, List<String> dataList) 
            throws ExecutionException, InterruptedException {
        
        GlideClientConfiguration.GlideClientConfigurationBuilder configBuilder = 
            GlideClientConfiguration.builder()
                .address(NodeAddress.builder().host(HOST).port(PORT).build());
        
        if (compressionConfig != null) {
            configBuilder.compression(compressionConfig);
        }
        
        try (GlideClient client = GlideClient.createClient(configBuilder.build()).get()) {
            // Warmup - use different entries for each warmup iteration
            for (int i = 0; i < WARMUP_ITERATIONS; i++) {
                String data = dataList.get(i % dataList.size());
                client.set(keyPrefix + "_warmup_" + i, data).get();
            }
            
            // Measure TPS
            long startTime = System.currentTimeMillis();
            int operations = 0;
            
            while (System.currentTimeMillis() - startTime < TPS_TEST_DURATION_MS) {
                String data = dataList.get(operations % dataList.size());
                client.set(keyPrefix + "_tps_" + operations, data).get();
                client.get(keyPrefix + "_tps_" + operations).get();
                operations += 2; // SET + GET
            }
            
            long endTime = System.currentTimeMillis();
            double tps = (operations * 1000.0) / (endTime - startTime);
            
            // Measure compression across all entries
            long totalCompressedSize = 0;
            int originalSize = 0;
            
            for (int i = 0; i < dataList.size(); i++) {
                String data = dataList.get(i);
                String testKey = keyPrefix + "_size_test_" + i;
                client.set(testKey, data).get();
                long memUsage = getMemoryUsage(testKey, client);
                totalCompressedSize += memUsage;
                originalSize += data.length();
                

            }
            
            // Handle case where memory usage couldn't be measured
            if (totalCompressedSize == 0) {
                totalCompressedSize = originalSize; // Fallback to original size
            }
            
            // For uncompressed data, ratio should be 1.0
            double compressionRatio;
            if (compressionConfig == null) {
                compressionRatio = 1.0; // No compression applied
            } else {
                compressionRatio = totalCompressedSize > 0 ? (double) originalSize / totalCompressedSize : 1.0;
            }
            
            return new BenchmarkResult(tps, totalCompressedSize, compressionRatio);
        }
    }
    
    /**
     * Measure memory usage for a configuration
     */
    private static long measureMemoryUsage(CompressionConfiguration compressionConfig, 
                                          String keyPrefix, List<String> dataList) 
            throws ExecutionException, InterruptedException {
        
        GlideClientConfiguration.GlideClientConfigurationBuilder configBuilder = 
            GlideClientConfiguration.builder()
                .address(NodeAddress.builder().host(HOST).port(PORT).build());
        
        if (compressionConfig != null) {
            configBuilder.compression(compressionConfig);
        }
        
        try (GlideClient client = GlideClient.createClient(configBuilder.build()).get()) {
            long totalMemory = 0;
            for (int i = 0; i < dataList.size(); i++) {
                String key = keyPrefix + "_" + i;
                client.set(key, dataList.get(i)).get();
                totalMemory += getMemoryUsage(key, client);
            }
            return totalMemory;
        }
    }
    
    /**
     * Create compression configuration
     */
    private static CompressionConfiguration createCompressionConfig(CompressionBackend backend, 
                                                                   int level, 
                                                                   int minSize) {
        return CompressionConfiguration.builder()
                .enabled(true)
                .backend(backend)
                .compressionLevel(level)
                .minCompressionSize(minSize)
                .build();
    }
    
    /**
     * Get memory usage for a key
     */
    private static long getMemoryUsage(String key, GlideClient client) {
        try {
            Object result = client.customCommand(new String[]{"MEMORY", "USAGE", key}).get();
            if (result instanceof Long) {
                return (Long) result;
            } else if (result instanceof Integer) {
                return ((Integer) result).longValue();
            } else if (result != null) {
                // Try to parse as string number
                try {
                    return Long.parseLong(result.toString());
                } catch (NumberFormatException nfe) {
                    // Fall through to return 0
                }
            }
            return 0;
        } catch (Exception e) {
            // Silently return 0 for cleaner output
            return 0;
        }
    }
    

    
    /**
     * Benchmark result container
     */
    private static class BenchmarkResult {
        final double tps;
        final long compressedSize;
        final double compressionRatio;
        
        BenchmarkResult(double tps, long compressedSize, double compressionRatio) {
            this.tps = tps;
            this.compressedSize = compressedSize;
            this.compressionRatio = compressionRatio;
        }
    }
}
