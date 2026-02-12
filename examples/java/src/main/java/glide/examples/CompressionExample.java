/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.examples;

import static glide.api.logging.Logger.Level.INFO;
import static glide.api.logging.Logger.log;

import glide.api.GlideClient;
import glide.api.logging.Logger;
import glide.api.models.configuration.CompressionBackend;
import glide.api.models.configuration.CompressionConfiguration;
import glide.api.models.configuration.GlideClientConfiguration;
import glide.api.models.configuration.NodeAddress;
import java.util.Map;

/**
 * Demonstrates how to create a GLIDE client with transparent compression enabled.
 *
 * <p>When compression is enabled, the client automatically compresses values for SET-type commands
 * and decompresses values for GET-type commands, reducing bandwidth and storage usage.
 *
 * <p>Usage: Ensure a Valkey server is running on localhost:6379, then run this example.
 */
public class CompressionExample {

    public static void main(String[] args) throws Exception {
        Logger.setLoggerConfig(INFO);

        // Create compression configuration
        CompressionConfiguration compressionConfig =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.ZSTD) // or CompressionBackend.LZ4
                        .compressionLevel(3) // optional, backend-specific
                        .minCompressionSize(64) // only compress values >= 64 bytes
                        .build();

        // Build client configuration with compression
        GlideClientConfiguration config =
                GlideClientConfiguration.builder()
                        .address(NodeAddress.builder().host("localhost").port(6379).build())
                        .compressionConfiguration(compressionConfig)
                        .requestTimeout(5000)
                        .build();

        try (GlideClient client = GlideClient.createClient(config).get()) {
            // Write a large value — it will be compressed transparently
            String largeValue = "A".repeat(10) + "B".repeat(10) + "C".repeat(10);
            largeValue = largeValue.repeat(100); // ~3KB of compressible data

            client.set("compression_demo_key", largeValue).get();
            log(INFO, "example", "SET completed with compression enabled");

            // Read it back — decompression is automatic
            String retrieved = client.get("compression_demo_key").get();
            if (!retrieved.equals(largeValue)) {
                throw new RuntimeException("Value mismatch after decompression");
            }
            log(INFO, "example", "GET returned correct decompressed value");

            // Check compression statistics
            Map<String, String> stats = client.getStatistics();
            log(INFO, "example", "Compression statistics:");
            log(INFO, "example", "  Values compressed:   " + stats.get("total_values_compressed"));
            log(INFO, "example", "  Values decompressed: " + stats.get("total_values_decompressed"));
            log(INFO, "example", "  Original bytes:      " + stats.get("total_original_bytes"));
            log(INFO, "example", "  Compressed bytes:    " + stats.get("total_bytes_compressed"));
            log(INFO, "example", "  Skipped (too small): " + stats.get("compression_skipped_count"));

            // Verify compression actually happened and reduced size
            long compressed = Long.parseLong(stats.get("total_values_compressed"));
            long originalBytes = Long.parseLong(stats.get("total_original_bytes"));
            long compressedBytes = Long.parseLong(stats.get("total_bytes_compressed"));
            if (compressed <= 0) {
                throw new RuntimeException("Expected at least one value to be compressed");
            }
            if (compressedBytes >= originalBytes) {
                throw new RuntimeException(
                        "Expected compressed bytes ("
                                + compressedBytes
                                + ") < original bytes ("
                                + originalBytes
                                + ")");
            }
            log(
                    INFO,
                    "example",
                    "Compression ratio: "
                            + String.format("%.1f%%", (1.0 - (double) compressedBytes / originalBytes) * 100));

            // Cleanup
            client.del(new String[] {"compression_demo_key"}).get();
            log(INFO, "example", "Cleanup complete");
        }
    }
}
