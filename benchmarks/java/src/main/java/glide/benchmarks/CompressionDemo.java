/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.benchmarks;

import glide.api.GlideClient;
import glide.api.models.configuration.CompressionBackend;
import glide.api.models.configuration.CompressionConfiguration;
import glide.api.models.configuration.GlideClientConfiguration;
import glide.api.models.configuration.NodeAddress;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

/**
 * Simple Java demo for testing GLIDE client with compression.
 * 
 * This demo shows basic compression functionality:
 * 1. Create GLIDE clients with compression configurations
 * 2. Test compression effectiveness with different data types
 * 3. Compare memory usage between compressed and uncompressed data
 * 
 * For comprehensive benchmarking, see CompressionBenchmark.java
 */
public class CompressionDemo {
    
    private static final String HOST = "localhost";
    private static final int PORT = 6379;
    
    public static void main(String[] args) {
        System.out.println("🚀 GLIDE Java Compression Demo");
        System.out.println("=" + "=".repeat(50));
        
        try {
            // Test different compression configurations
            testBasicCompression();
            testCompressionLevels();
            testCompressionBackends();
            testCompressionThresholds();
            testCompressionEffectiveness();
            
            System.out.println("\n🎉 Demo completed successfully!");
            System.out.println("\n💡 For comprehensive benchmarking with TPS measurements,");
            System.out.println("   realistic datasets, and detailed analysis, run:");
            System.out.println("   ./run_compression_benchmark.sh");
            
        } catch (Exception e) {
            System.err.println("\n❌ Error during demo: " + e.getClass().getSimpleName() + ": " + e.getMessage());
            // Don't print full stack trace for cleaner output
        }
    }
    
    /**
     * Test basic compression functionality
     */
    private static void testBasicCompression() throws ExecutionException, InterruptedException {
        System.out.println("\n🔧 Testing Basic Compression");
        System.out.println("-".repeat(30));
        
        // Create compression configuration
        CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .compressionLevel(3)
                .minCompressionSize(64)
                .build();
        
        // Create client configuration
        GlideClientConfiguration config = GlideClientConfiguration.builder()
                .address(NodeAddress.builder().host(HOST).port(PORT).build())
                .compression(compressionConfig)
                .build();
        
        try (GlideClient client = GlideClient.createClient(config).get()) {
            // Test small data (should not be compressed)
            String smallData = "small";
            client.set("test_small", smallData).get();
            String retrievedSmall = client.get("test_small").get();
            System.out.println("✅ Small data: " + smallData + " -> " + retrievedSmall);
            
            // Test large data (should be compressed)
            String largeData = "This is some compressible data that should benefit from compression! ".repeat(20);
            client.set("test_large", largeData).get();
            String retrievedLarge = client.get("test_large").get();
            System.out.println("✅ Large data length: " + largeData.length() + " chars");
            System.out.println("✅ Retrieved matches: " + largeData.equals(retrievedLarge));
            
            // Check memory usage
            checkMemoryUsage(client, "test_small", "test_large");
        }
    }
    
    /**
     * Test different compression levels
     */
    private static void testCompressionLevels() throws ExecutionException, InterruptedException {
        System.out.println("\n🎚️ Testing Compression Levels");
        System.out.println("-".repeat(30));
        
        String testData = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. ".repeat(50);
        int[] levels = {1, 3, 6, 9, 15, 22};
        
        for (int level : levels) {
            CompressionConfiguration config = CompressionConfiguration.builder()
                    .enabled(true)
                    .backend(CompressionBackend.ZSTD)
                    .compressionLevel(level)
                    .minCompressionSize(64)
                    .build();
            
            GlideClientConfiguration clientConfig = GlideClientConfiguration.builder()
                    .address(NodeAddress.builder().host(HOST).port(PORT).build())
                    .compression(config)
                    .build();
            
            try (GlideClient client = GlideClient.createClient(clientConfig).get()) {
                String key = "test_level_" + level;
                
                long startTime = System.nanoTime();
                client.set(key, testData).get();
                client.get(key).get();
                long endTime = System.nanoTime();
                
                long memoryUsage = getMemoryUsage(key, client);
                double compressionTime = (endTime - startTime) / 1_000_000.0; // ms
                
                System.out.printf("Level %2d: %d bytes in Redis, %.2f ms%n", 
                    level, memoryUsage, compressionTime);
            }
        }
    }
    
    /**
     * Test ZSTD compression backend (LZ4 not yet implemented)
     */
    private static void testCompressionBackends() throws ExecutionException, InterruptedException {
        System.out.println("\n🔄 Testing ZSTD Compression Backend");
        System.out.println("-".repeat(30));
        
        String testData = "Compressible data for backend testing! ".repeat(100);
        
        CompressionConfiguration config = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .compressionLevel(3)
                .minCompressionSize(64)
                .build();
        
        GlideClientConfiguration clientConfig = GlideClientConfiguration.builder()
                .address(NodeAddress.builder().host(HOST).port(PORT).build())
                .compression(config)
                .build();
        
        try (GlideClient client = GlideClient.createClient(clientConfig).get()) {
            String key = "test_backend_zstd";
            
            long startTime = System.nanoTime();
            client.set(key, testData).get();
            String retrieved = client.get(key).get();
            long endTime = System.nanoTime();
            
            long memoryUsage = getMemoryUsage(key, client);
            double totalTime = (endTime - startTime) / 1_000_000.0; // ms
            
            System.out.printf("ZSTD: %d bytes, %.2f ms, data matches: %s%n", 
                memoryUsage, totalTime, testData.equals(retrieved));
            
            System.out.println("Note: LZ4 backend is not yet implemented");
        }
    }
    
    /**
     * Test compression size thresholds
     */
    private static void testCompressionThresholds() throws ExecutionException, InterruptedException {
        System.out.println("\n📏 Testing Compression Thresholds");
        System.out.println("-".repeat(30));
        
        int[] thresholds = {32, 64, 128, 256};
        String baseData = "x";
        
        for (int threshold : thresholds) {
            CompressionConfiguration config = CompressionConfiguration.builder()
                    .enabled(true)
                    .backend(CompressionBackend.ZSTD)
                    .compressionLevel(3)
                    .minCompressionSize(threshold)
                    .build();
            
            GlideClientConfiguration clientConfig = GlideClientConfiguration.builder()
                    .address(NodeAddress.builder().host(HOST).port(PORT).build())
                    .compression(config)
                    .build();
            
            try (GlideClient client = GlideClient.createClient(clientConfig).get()) {
                // Test data just below threshold
                String smallData = baseData.repeat(threshold - 10);
                String smallKey = "threshold_small_" + threshold;
                client.set(smallKey, smallData).get();
                
                // Test data above threshold
                String largeData = baseData.repeat(threshold + 100);
                String largeKey = "threshold_large_" + threshold;
                client.set(largeKey, largeData).get();
                
                long smallMemory = getMemoryUsage(smallKey, client);
                long largeMemory = getMemoryUsage(largeKey, client);
                
                System.out.printf("Threshold %d: small(%d bytes) -> %d, large(%d bytes) -> %d%n",
                    threshold, smallData.length(), smallMemory, largeData.length(), largeMemory);
            }
        }
    }
    
    /**
     * Test compression effectiveness with different data types
     */
    private static void testCompressionEffectiveness() throws ExecutionException, InterruptedException {
        System.out.println("\n📊 Testing Compression Effectiveness");
        System.out.println("-".repeat(30));
        
        CompressionConfiguration compressedConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .compressionLevel(3)
                .minCompressionSize(64)
                .build();
        
        GlideClientConfiguration clientConfig = GlideClientConfiguration.builder()
                .address(NodeAddress.builder().host(HOST).port(PORT).build())
                .compression(compressedConfig)
                .build();
        
        // Uncompressed client for comparison
        GlideClientConfiguration uncompressedConfig = GlideClientConfiguration.builder()
                .address(NodeAddress.builder().host(HOST).port(PORT).build())
                .build();
        
        try (GlideClient compressedClient = GlideClient.createClient(clientConfig).get();
             GlideClient uncompressedClient = GlideClient.createClient(uncompressedConfig).get()) {
            
            // Test different data types
            String[] testCases = {
                "Highly repetitive data! ".repeat(200),
                generateJsonData(1000),
                generateRandomData(5000),
                "Mixed content with numbers 123456789 and text that repeats often. ".repeat(50)
            };
            
            String[] caseNames = {"Repetitive", "JSON", "Random", "Mixed"};
            
            for (int i = 0; i < testCases.length; i++) {
                String data = testCases[i];
                String caseName = caseNames[i];
                
                String compressedKey = "effectiveness_compressed_" + i;
                String uncompressedKey = "effectiveness_uncompressed_" + i;
                
                // Store with compression
                compressedClient.set(compressedKey, data).get();
                long compressedMemory = getMemoryUsage(compressedKey, compressedClient);
                
                // Store without compression
                uncompressedClient.set(uncompressedKey, data).get();
                long uncompressedMemory = getMemoryUsage(uncompressedKey, uncompressedClient);
                
                double ratio = (double) uncompressedMemory / compressedMemory;
                double savings = ((double) (uncompressedMemory - compressedMemory) / uncompressedMemory) * 100;
                
                System.out.printf("%s: %d -> %d bytes (%.2fx compression, %.1f%% saved)%n",
                    caseName, uncompressedMemory, compressedMemory, ratio, savings);
            }
        }
    }
    
    /**
     * Generate JSON-like data for testing
     */
    private static String generateJsonData(int entries) {
        StringBuilder json = new StringBuilder("{");
        for (int i = 0; i < entries; i++) {
            if (i > 0) json.append(",");
            json.append("\"key").append(i).append("\":\"value").append(i).append("_data\"");
        }
        json.append("}");
        return json.toString();
    }
    
    /**
     * Generate random-ish data (less compressible)
     */
    private static String generateRandomData(int length) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < length; i++) {
            sb.append((char) ('a' + (i * 7) % 26));
        }
        return sb.toString();
    }
    
    /**
     * Check memory usage for keys using GLIDE client
     */
    private static void checkMemoryUsage(GlideClient client, String... keys) {
        for (String key : keys) {
            long memory = getMemoryUsage(key, client);
            System.out.println("💾 " + key + ": " + memory + " bytes");
        }
    }
    
    /**
     * Get memory usage for a single key using GLIDE custom command
     */
    private static long getMemoryUsage(String key, GlideClient client) {
        try {
            Object result = client.customCommand(new String[]{"MEMORY", "USAGE", key}).get();
            if (result instanceof Long) {
                return (Long) result;
            }
            return 0;
        } catch (Exception e) {
            System.err.println("⚠️ Could not get memory usage for " + key + ": " + e.getMessage());
            return 0;
        }
    }
}
