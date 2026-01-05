/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.examples;

import glide.api.GlideClient;
import glide.api.models.configuration.CompressionBackend;
import glide.api.models.configuration.CompressionConfiguration;
import glide.api.models.configuration.GlideClientConfiguration;
import glide.api.models.configuration.NodeAddress;
import java.util.Map;
import java.util.UUID;

/**
 * Example demonstrating compression features in Valkey GLIDE.
 *
 * <p>Compression reduces bandwidth usage and storage requirements by automatically compressing
 * values on SET operations and decompressing on GET operations.
 */
public class CompressionExample {

    public static void main(String[] args) {
        System.out.println("=== Valkey GLIDE Compression Examples ===\n");

        // Example 1: Basic compression with defaults
        basicCompressionExample();

        // Example 2: Custom compression settings
        customCompressionExample();

        // Example 3: Monitoring compression statistics
        compressionStatisticsExample();

        // Example 4: Comparing backends
        backendComparisonExample();
    }

    /**
     * Example 1: Basic compression with default settings.
     *
     * <p>Uses ZSTD compression with default level (3) and minimum size (64 bytes).
     */
    private static void basicCompressionExample() {
        System.out.println("Example 1: Basic Compression with Defaults");
        System.out.println("-------------------------------------------");

        // Enable compression with default settings
        CompressionConfiguration compression =
                CompressionConfiguration.builder().enabled(true).build();

        GlideClientConfiguration config =
                GlideClientConfiguration.builder()
                        .address(NodeAddress.builder().host("localhost").port(6379).build())
                        .compression(compression)
                        .build();

        try (GlideClient client = GlideClient.createClient(config).get()) {
            String key = "compression:example1:" + UUID.randomUUID();

            // Store a large compressible value
            String largeValue = generateCompressibleText(10000); // 10KB of compressible text
            client.set(key, largeValue).get();

            // Retrieve the value (automatically decompressed)
            String retrieved = client.get(key).get();

            System.out.println("✓ Stored and retrieved " + largeValue.length() + " bytes");
            System.out.println("✓ Values match: " + largeValue.equals(retrieved));

            // Clean up
            client.del(new String[] {key}).get();
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
        }

        System.out.println();
    }

    /**
     * Example 2: Custom compression settings.
     *
     * <p>Demonstrates using LZ4 backend with custom compression level and minimum size.
     */
    private static void customCompressionExample() {
        System.out.println("Example 2: Custom Compression Settings");
        System.out.println("--------------------------------------");

        // Configure LZ4 compression with custom settings
        CompressionConfiguration compression =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.LZ4) // Use LZ4 for faster compression
                        .compressionLevel(6) // Higher level for better compression
                        .minCompressionSize(128) // Only compress values >= 128 bytes
                        .build();

        GlideClientConfiguration config =
                GlideClientConfiguration.builder()
                        .address(NodeAddress.builder().host("localhost").port(6379).build())
                        .compression(compression)
                        .build();

        try (GlideClient client = GlideClient.createClient(config).get()) {
            String keyLarge = "compression:example2:large:" + UUID.randomUUID();
            String keySmall = "compression:example2:small:" + UUID.randomUUID();

            // Store a large value (will be compressed)
            String largeValue = generateCompressibleText(5000);
            client.set(keyLarge, largeValue).get();

            // Store a small value (will NOT be compressed due to minCompressionSize)
            String smallValue = "small";
            client.set(keySmall, smallValue).get();

            System.out.println("✓ Large value (" + largeValue.length() + " bytes): compressed");
            System.out.println("✓ Small value (" + smallValue.length() + " bytes): not compressed");

            // Clean up
            client.del(new String[] {keyLarge, keySmall}).get();
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
        }

        System.out.println();
    }

    /**
     * Example 3: Monitoring compression statistics.
     *
     * <p>Shows how to access and interpret compression statistics.
     */
    private static void compressionStatisticsExample() {
        System.out.println("Example 3: Compression Statistics");
        System.out.println("----------------------------------");

        CompressionConfiguration compression =
                CompressionConfiguration.builder().enabled(true).build();

        GlideClientConfiguration config =
                GlideClientConfiguration.builder()
                        .address(NodeAddress.builder().host("localhost").port(6379).build())
                        .compression(compression)
                        .build();

        try (GlideClient client = GlideClient.createClient(config).get()) {
            // Perform some operations
            for (int i = 0; i < 10; i++) {
                String key = "compression:example3:" + i + ":" + UUID.randomUUID();
                String value = generateCompressibleText(1000 * (i + 1)); // 1KB to 10KB
                client.set(key, value).get();
                client.get(key).get();
                client.del(new String[] {key}).get();
            }

            // Get compression statistics
            Map<String, String> stats = client.getStatistics();

            System.out.println("Compression Statistics:");
            System.out.println(
                    "  Values compressed:   " + stats.getOrDefault("total_values_compressed", "0"));
            System.out.println(
                    "  Values decompressed: " + stats.getOrDefault("total_values_decompressed", "0"));
            System.out.println(
                    "  Original bytes:      " + stats.getOrDefault("total_original_bytes", "0"));
            System.out.println(
                    "  Compressed bytes:    " + stats.getOrDefault("total_bytes_compressed", "0"));
            System.out.println(
                    "  Compression skipped: " + stats.getOrDefault("compression_skipped_count", "0"));

            // Calculate compression ratio
            long originalBytes = Long.parseLong(stats.getOrDefault("total_original_bytes", "0"));
            long compressedBytes = Long.parseLong(stats.getOrDefault("total_bytes_compressed", "0"));

            if (originalBytes > 0 && compressedBytes > 0) {
                double ratio = (double) originalBytes / compressedBytes;
                double savings = (1.0 - ((double) compressedBytes / originalBytes)) * 100;
                System.out.printf("  Compression ratio:   %.2fx%n", ratio);
                System.out.printf("  Space savings:       %.1f%%%n", savings);
            }
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
        }

        System.out.println();
    }

    /**
     * Example 4: Comparing ZSTD and LZ4 backends.
     *
     * <p>Demonstrates the trade-offs between compression ratio and speed.
     */
    private static void backendComparisonExample() {
        System.out.println("Example 4: Backend Comparison (ZSTD vs LZ4)");
        System.out.println("--------------------------------------------");

        String testData = generateCompressibleText(50000); // 50KB test data

        // Test ZSTD
        System.out.println("Testing ZSTD backend...");
        testBackend(CompressionBackend.ZSTD, 3, testData);

        // Test LZ4
        System.out.println("Testing LZ4 backend...");
        testBackend(CompressionBackend.LZ4, 0, testData);

        System.out.println(
                "Note: ZSTD typically provides better compression ratios, while LZ4 is faster.");
        System.out.println();
    }

    /**
     * Helper method to test a specific compression backend.
     *
     * @param backend The compression backend to test
     * @param level The compression level
     * @param testData The data to compress
     */
    private static void testBackend(CompressionBackend backend, int level, String testData) {
        CompressionConfiguration compression =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(backend)
                        .compressionLevel(level)
                        .build();

        GlideClientConfiguration config =
                GlideClientConfiguration.builder()
                        .address(NodeAddress.builder().host("localhost").port(6379).build())
                        .compression(compression)
                        .build();

        try (GlideClient client = GlideClient.createClient(config).get()) {
            String key = "compression:example4:" + backend + ":" + UUID.randomUUID();

            // Measure write time
            long startWrite = System.nanoTime();
            client.set(key, testData).get();
            long writeTime = System.nanoTime() - startWrite;

            // Measure read time
            long startRead = System.nanoTime();
            client.get(key).get();
            long readTime = System.nanoTime() - startRead;

            // Get statistics
            Map<String, String> stats = client.getStatistics();
            long originalBytes = Long.parseLong(stats.getOrDefault("total_original_bytes", "0"));
            long compressedBytes = Long.parseLong(stats.getOrDefault("total_bytes_compressed", "0"));

            System.out.printf(
                    "  %s: Write=%.2fms, Read=%.2fms, Ratio=%.2fx%n",
                    backend,
                    writeTime / 1_000_000.0,
                    readTime / 1_000_000.0,
                    originalBytes > 0 ? (double) originalBytes / compressedBytes : 0.0);

            // Clean up
            client.del(new String[] {key}).get();
        } catch (Exception e) {
            System.err.println("  Error testing " + backend + ": " + e.getMessage());
        }
    }

    /**
     * Generates compressible text data.
     *
     * <p>Creates text with repeated patterns that compress well.
     *
     * @param sizeBytes Target size in bytes
     * @return Generated text
     */
    private static String generateCompressibleText(int sizeBytes) {
        String pattern =
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                        + "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ";

        StringBuilder sb = new StringBuilder(sizeBytes);
        while (sb.length() < sizeBytes) {
            sb.append(pattern);
        }

        return sb.substring(0, Math.min(sizeBytes, sb.length()));
    }
}
