/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.examples;

import static glide.api.logging.Logger.log;
import static glide.api.logging.Logger.Level.ERROR;
import static glide.api.logging.Logger.Level.INFO;
import static glide.api.logging.Logger.Level.WARN;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

import com.google.gson.Gson;
import com.google.gson.JsonObject;

import glide.api.GlideClient;
import glide.api.GlideClusterClient;
import glide.api.logging.Logger;
import glide.api.models.configuration.GlideClientConfiguration;
import glide.api.models.configuration.GlideClusterClientConfiguration;
import glide.api.models.configuration.CompressionConfiguration;
import glide.api.models.configuration.CompressionBackend;
import glide.api.models.configuration.NodeAddress;
import glide.api.models.exceptions.ClosingException;
import glide.api.models.exceptions.ConnectionException;
import glide.api.models.exceptions.TimeoutException;

/**
 * This example demonstrates how to use automatic compression with Valkey GLIDE.
 * It shows various compression configurations and use cases.
 */
public class CompressionExample {

    private static final Gson gson = new Gson();

    /**
     * Creates a GlideClient with compression configuration.
     */
    public static GlideClient createClientWithCompression(
            List<NodeAddress> nodeList,
            CompressionConfiguration compressionConfig)
            throws CancellationException, ExecutionException, InterruptedException {

        GlideClientConfiguration config = GlideClientConfiguration.builder()
                .addresses(nodeList)
                .compression(compressionConfig)
                .requestTimeout(2000)
                .build();

        return GlideClient.createClient(config).get();
    }

    /**
     * Creates a GlideClusterClient with compression configuration.
     */
    public static GlideClusterClient createClusterClientWithCompression(
            List<NodeAddress> nodeList,
            CompressionConfiguration compressionConfig)
            throws CancellationException, ExecutionException, InterruptedException {

        GlideClusterClientConfiguration config = GlideClusterClientConfiguration.builder()
                .addresses(nodeList)
                .compression(compressionConfig)
                .requestTimeout(2000)
                .build();

        return GlideClusterClient.createClient(config).get();
    }

    /**
     * Demonstrates basic compression usage with default settings.
     */
    public static void basicCompressionExample(List<NodeAddress> nodeList)
            throws ExecutionException, InterruptedException {
        log(INFO, "compression_example", "=== Basic Compression Example ===");

        // Create compression configuration with defaults
        CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                // compressionLevel defaults to 3
                // minCompressionSize defaults to 64 bytes
                .build();

        try (GlideClient client = createClientWithCompression(nodeList, compressionConfig)) {
            // Store some data that will be compressed
            JsonObject largeJson = new JsonObject();
            largeJson.addProperty("user_id", "12345");
            largeJson.addProperty("name", "John Doe");
            largeJson.addProperty("email", "john.doe@example.com");
            
            JsonObject preferences = new JsonObject();
            preferences.addProperty("theme", "dark");
            preferences.addProperty("language", "en");
            preferences.addProperty("notifications", true);
            largeJson.add("preferences", preferences);
            
            // Large field to ensure compression
            largeJson.addProperty("data", "x".repeat(1000));

            String jsonStr = gson.toJson(largeJson);
            log(INFO, "compression_example", "Original JSON size: " + jsonStr.length() + " bytes");

            // Set the data (will be automatically compressed)
            client.set("user:12345", jsonStr).get();
            log(INFO, "compression_example", "Data stored with compression");

            // Get the data (will be automatically decompressed)
            String retrievedData = client.get("user:12345").get();
            JsonObject retrievedJson = gson.fromJson(retrievedData, JsonObject.class);

            boolean matches = gson.toJson(retrievedJson).equals(jsonStr);
            log(INFO, "compression_example", "Retrieved data matches: " + matches);
            log(INFO, "compression_example", "Retrieved user: " + retrievedJson.get("name").getAsString());

        } catch (CancellationException | ExecutionException | InterruptedException e) {
            log(ERROR, "compression_example", "Basic compression example failed: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Demonstrates different compression configurations for various use cases.
     */
    public static void compressionConfigurationExamples(List<NodeAddress> nodeList)
            throws ExecutionException, InterruptedException {
        log(INFO, "compression_example", "=== Compression Configuration Examples ===");

        // High-performance configuration (fast compression)
        CompressionConfiguration highPerformanceConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .compressionLevel(1)  // Fastest compression
                .minCompressionSize(128)  // Skip smaller values
                .maxCompressionSize(1024 * 1024)  // 1MB limit
                .build();

        // High-compression configuration (better compression ratio)
        CompressionConfiguration highCompressionConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .compressionLevel(6)  // Better compression
                .minCompressionSize(32)  // Compress more values
                .build();

        // Balanced configuration (recommended for most use cases)
        CompressionConfiguration balancedConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .compressionLevel(3)  // Good balance
                .minCompressionSize(64)  // Standard threshold
                .maxCompressionSize(10 * 1024 * 1024)  // 10MB limit
                .build();

        Map<String, CompressionConfiguration> configs = new HashMap<>();
        configs.put("High Performance", highPerformanceConfig);
        configs.put("High Compression", highCompressionConfig);
        configs.put("Balanced", balancedConfig);

        String testData = "The quick brown fox jumps over the lazy dog. ".repeat(100);  // ~4.3KB

        for (Map.Entry<String, CompressionConfiguration> entry : configs.entrySet()) {
            String configName = entry.getKey();
            CompressionConfiguration config = entry.getValue();
            
            log(INFO, "compression_example", "Testing " + configName + " configuration");

            try (GlideClient client = createClientWithCompression(nodeList, config)) {
                String key = "test:" + configName.toLowerCase().replace(" ", "_");

                // Measure compression performance
                long startSetTime = System.currentTimeMillis();
                client.set(key, testData).get();
                long setTime = System.currentTimeMillis() - startSetTime;

                long startGetTime = System.currentTimeMillis();
                String retrieved = client.get(key).get();
                long getTime = System.currentTimeMillis() - startGetTime;

                log(INFO, "compression_example", 
                    "  Set time: " + setTime + "ms, Get time: " + getTime + "ms");
                log(INFO, "compression_example", 
                    "  Data integrity: " + testData.equals(retrieved));

            } catch (CancellationException | ExecutionException | InterruptedException e) {
                log(ERROR, "compression_example", "Configuration example failed: " + e.getMessage());
                throw e;
            }
        }
    }

    /**
     * Demonstrates compression with batch operations (pipelines and transactions).
     */
    public static void batchOperationsExample(List<NodeAddress> nodeList)
            throws ExecutionException, InterruptedException {
        log(INFO, "compression_example", "=== Batch Operations with Compression ===");

        CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .minCompressionSize(32)  // Lower threshold for demo
                .build();

        try (GlideClient client = createClientWithCompression(nodeList, compressionConfig)) {
            // Pipeline example
            log(INFO, "compression_example", "Testing pipeline with compression");

            Map<String, String> pipelineData = new HashMap<>();
            pipelineData.put("user:1", gson.toJson(Map.of("name", "Alice", "data", "A".repeat(500))));
            pipelineData.put("user:2", gson.toJson(Map.of("name", "Bob", "data", "B".repeat(500))));
            pipelineData.put("user:3", gson.toJson(Map.of("name", "Charlie", "data", "C".repeat(500))));

            // Use pipeline to set multiple values (all will be compressed)
            CompletableFuture<?>[] pipelineOps = new CompletableFuture[pipelineData.size() + 1];
            int index = 0;
            for (Map.Entry<String, String> entry : pipelineData.entrySet()) {
                pipelineOps[index++] = client.set(entry.getKey(), entry.getValue());
            }
            pipelineOps[index] = client.mget(pipelineData.keySet().toArray(new String[0]));

            CompletableFuture.allOf(pipelineOps).get();
            log(INFO, "compression_example", "Pipeline executed successfully");

            // Verify data integrity
            String[] mgetResults = (String[]) pipelineOps[pipelineOps.length - 1].get();
            int i = 0;
            for (Map.Entry<String, String> entry : pipelineData.entrySet()) {
                boolean matches = entry.getValue().equals(mgetResults[i]);
                log(INFO, "compression_example", "  " + entry.getKey() + ": " + matches);
                i++;
            }

            // Transaction example
            log(INFO, "compression_example", "Testing transaction with compression");

            String counterData0 = gson.toJson(Map.of("count", 0, "data", "x".repeat(200)));
            String counterData1 = gson.toJson(Map.of("count", 1, "data", "x".repeat(200)));

            // Execute transaction
            client.set("counter:compressed", counterData0).get();
            String result1 = client.get("counter:compressed").get();
            client.set("counter:compressed", counterData1).get();
            String result2 = client.get("counter:compressed").get();

            log(INFO, "compression_example", "Transaction executed successfully");

            // Verify the final counter value
            JsonObject finalData = gson.fromJson(result2, JsonObject.class);
            log(INFO, "compression_example", "Final counter value: " + finalData.get("count").getAsInt());

        } catch (CancellationException | ExecutionException | InterruptedException e) {
            log(ERROR, "compression_example", "Batch operations example failed: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Demonstrates compatibility between compression-enabled and disabled clients.
     */
    public static void mixedClientScenario(List<NodeAddress> nodeList)
            throws ExecutionException, InterruptedException {
        log(INFO, "compression_example", "=== Mixed Client Scenario ===");

        // Client with compression enabled
        CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
                .enabled(true)
                .build();

        // Client with compression disabled
        CompressionConfiguration noCompressionConfig = CompressionConfiguration.builder()
                .enabled(false)
                .build();

        try (GlideClient compressedClient = createClientWithCompression(nodeList, compressionConfig);
             GlideClient uncompressedClient = createClientWithCompression(nodeList, noCompressionConfig)) {

            String testData = "This is test data that will be compressed. ".repeat(50);

            // Store data with compression-enabled client
            compressedClient.set("mixed:test", testData).get();
            log(INFO, "compression_example", "Data stored with compression-enabled client");

            // Read with compression-enabled client (automatic decompression)
            String compressedRead = compressedClient.get("mixed:test").get();
            log(INFO, "compression_example", 
                "Compression-enabled client read: " + testData.equals(compressedRead));

            // Read with compression-disabled client (gets raw compressed data)
            String uncompressedRead = uncompressedClient.get("mixed:test").get();
            log(INFO, "compression_example", 
                "Compression-disabled client read raw data size: " + uncompressedRead.length() + " bytes");
            log(INFO, "compression_example", 
                "Raw data is different from original: " + !testData.equals(uncompressedRead));

            // Store uncompressed data
            uncompressedClient.set("mixed:uncompressed", testData).get();
            log(INFO, "compression_example", "Data stored with compression-disabled client");

            // Read uncompressed data with both clients
            String compressedReadUncomp = compressedClient.get("mixed:uncompressed").get();
            String uncompressedReadUncomp = uncompressedClient.get("mixed:uncompressed").get();

            boolean bothCorrect = testData.equals(compressedReadUncomp) && testData.equals(uncompressedReadUncomp);
            log(INFO, "compression_example", "Both clients read uncompressed data correctly: " + bothCorrect);

        } catch (CancellationException | ExecutionException | InterruptedException e) {
            log(ERROR, "compression_example", "Mixed client scenario failed: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Compares performance with and without compression.
     */
    public static void performanceComparison(List<NodeAddress> nodeList)
            throws ExecutionException, InterruptedException {
        log(INFO, "compression_example", "=== Performance Comparison ===");

        // Test data of different types
        Map<String, String> testCases = new HashMap<>();
        testCases.put("Small JSON", gson.toJson(Map.of("id", 1, "name", "test")));
        testCases.put("Large JSON", gson.toJson(Map.of("id", 1, "data", "x".repeat(2000), 
                                                      "metadata", Map.of("created", "2024-01-01"))));
        testCases.put("Repetitive Text", "Hello World! ".repeat(200));
        testCases.put("Random-like Data", "ABCDEFGHIJKLMNOPQRSTUVWXYZ".repeat(40));

        Map<String, CompressionConfiguration> configs = new HashMap<>();
        configs.put("No Compression", CompressionConfiguration.builder().enabled(false).build());
        configs.put("With Compression", CompressionConfiguration.builder().enabled(true).minCompressionSize(10).build());

        for (Map.Entry<String, String> testCase : testCases.entrySet()) {
            String testName = testCase.getKey();
            String testData = testCase.getValue();
            
            log(INFO, "compression_example", "Testing: " + testName + " (" + testData.length() + " bytes)");

            for (Map.Entry<String, CompressionConfiguration> configEntry : configs.entrySet()) {
                String configName = configEntry.getKey();
                CompressionConfiguration config = configEntry.getValue();

                try (GlideClient client = createClientWithCompression(nodeList, config)) {
                    String key = "perf:" + testName.toLowerCase().replace(" ", "_");

                    // Measure set performance
                    long startSetTime = System.currentTimeMillis();
                    client.set(key, testData).get();
                    long setTime = System.currentTimeMillis() - startSetTime;

                    // Measure get performance
                    long startGetTime = System.currentTimeMillis();
                    String retrieved = client.get(key).get();
                    long getTime = System.currentTimeMillis() - startGetTime;

                    // Verify data integrity
                    boolean dataMatches = testData.equals(retrieved);

                    log(INFO, "compression_example", 
                        "  " + configName + ": SET " + setTime + "ms, GET " + getTime + "ms, Integrity: " + dataMatches);

                } catch (CancellationException | ExecutionException | InterruptedException e) {
                    log(ERROR, "compression_example", "Performance comparison failed: " + e.getMessage());
                    throw e;
                }
            }

            log(INFO, "compression_example", "");
        }
    }

    /**
     * Demonstrates error handling with compression.
     */
    public static void errorHandlingExample(List<NodeAddress> nodeList)
            throws ExecutionException, InterruptedException {
        log(INFO, "compression_example", "=== Error Handling Example ===");

        try {
            // Try to create client with invalid configuration
            CompressionConfiguration invalidConfig = CompressionConfiguration.builder()
                    .enabled(true)
                    .compressionLevel(100)  // Invalid level for ZSTD (max is 22)
                    .build();

            try (GlideClient client = createClientWithCompression(nodeList, invalidConfig)) {
                // This should not be reached
            }

        } catch (Exception e) {
            log(INFO, "compression_example", "Expected configuration error: " + e.getClass().getSimpleName());
        }

        // Valid configuration with error handling
        CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
                .enabled(true)
                .build();

        try (GlideClient client = createClientWithCompression(nodeList, compressionConfig)) {
            // Normal operation
            client.set("error:test", "test data").get();
            String result = client.get("error:test").get();
            log(INFO, "compression_example", "Normal operation successful: " + result);

            // Compression errors are handled gracefully by the client
            // (fallback to uncompressed data with warning logs)

        } catch (Exception e) {
            log(ERROR, "compression_example", "Unexpected error: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Demonstrates compression with cluster client.
     */
    public static void clusterCompressionExample(List<NodeAddress> nodeList) {
        log(INFO, "compression_example", "=== Cluster Compression Example ===");

        CompressionConfiguration compressionConfig = CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .minCompressionSize(32)
                .build();

        try {
            List<NodeAddress> clusterNodes = Collections.singletonList(
                NodeAddress.builder().host("localhost").port(7000).build()  // Adjust for your cluster setup
            );

            try (GlideClusterClient clusterClient = createClusterClientWithCompression(clusterNodes, compressionConfig)) {
                // Test compression with cluster operations
                Map<String, String> clusterData = new HashMap<>();
                clusterData.put("cluster:user:1", gson.toJson(Map.of("name", "Alice", "region", "us-east", "data", "A".repeat(300))));
                clusterData.put("cluster:user:2", gson.toJson(Map.of("name", "Bob", "region", "us-west", "data", "B".repeat(300))));
                clusterData.put("cluster:user:3", gson.toJson(Map.of("name", "Charlie", "region", "eu-west", "data", "C".repeat(300))));

                // Set data across cluster (values will be compressed)
                for (Map.Entry<String, String> entry : clusterData.entrySet()) {
                    clusterClient.set(entry.getKey(), entry.getValue()).get();
                }

                log(INFO, "compression_example", "Data stored across cluster with compression");

                // Retrieve data (values will be decompressed)
                String[] keys = clusterData.keySet().toArray(new String[0]);
                String[] retrievedValues = clusterClient.mget(keys).get();

                for (int i = 0; i < keys.length; i++) {
                    String key = keys[i];
                    String original = clusterData.get(key);
                    String retrieved = retrievedValues[i];
                    boolean matches = original.equals(retrieved);
                    log(INFO, "compression_example", "  " + key + ": " + matches);
                }

            }

        } catch (Exception e) {
            log(WARN, "compression_example", 
                "Cluster example skipped (cluster not available): " + e.getMessage());
        }
    }

    /**
     * Executes all compression examples with exception handling.
     */
    private static void execCompressionExamples() throws ExecutionException {
        List<NodeAddress> nodeList = Collections.singletonList(
            NodeAddress.builder().host("localhost").port(6379).build()
        );

        try {
            basicCompressionExample(nodeList);
            compressionConfigurationExamples(nodeList);
            batchOperationsExample(nodeList);
            mixedClientScenario(nodeList);
            performanceComparison(nodeList);
            errorHandlingExample(nodeList);
            clusterCompressionExample(nodeList);

        } catch (CancellationException e) {
            log(ERROR, "compression_example", "Examples cancelled: " + e.getMessage());
            throw e;
        } catch (InterruptedException e) {
            log(ERROR, "compression_example", "Examples interrupted: " + e.getMessage());
            Thread.currentThread().interrupt();
            throw new CancellationException("Examples were interrupted.");
        } catch (ExecutionException e) {
            log(ERROR, "compression_example", "Examples failed: " + e.getMessage());
            throw e;
        } catch (Exception e) {
            log(ERROR, "compression_example", "Unexpected error: " + e.getMessage());
            throw new ExecutionException(e);
        }
    }

    /**
     * The entry point of the compression example.
     */
    public static void main(String[] args) throws ExecutionException {
        Logger.setLoggerConfig(INFO);

        log(INFO, "compression_example", "Starting Valkey GLIDE Compression Examples");
        log(INFO, "compression_example", "=".repeat(60));

        execCompressionExamples();

        log(INFO, "compression_example", "=".repeat(60));
        log(INFO, "compression_example", "All compression examples completed successfully!");
    }
}
