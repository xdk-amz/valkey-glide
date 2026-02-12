/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide;

import static glide.TestUtilities.commonClientConfig;
import static glide.TestUtilities.commonClusterClientConfig;
import static glide.api.BaseClient.OK;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import glide.api.BaseClient;
import glide.api.GlideClient;
import glide.api.GlideClusterClient;
import glide.api.models.Batch;
import glide.api.models.ClusterBatch;
import glide.api.models.configuration.CompressionBackend;
import glide.api.models.configuration.CompressionConfiguration;
import glide.api.models.exceptions.ConfigurationError;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutionException;
import java.util.stream.Stream;
import lombok.SneakyThrows;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

@Timeout(30)
public class CompressionTests {

    private static GlideClient standaloneClient;
    private static GlideClusterClient clusterClient;
    private static GlideClient standaloneClientNoCompression;
    private static GlideClusterClient clusterClientNoCompression;
    private static GlideClient standaloneClientLz4;

    private static CompressionConfiguration zstdConfig() {
        return CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.ZSTD)
                .compressionLevel(3)
                .minCompressionSize(64)
                .build();
    }

    private static CompressionConfiguration lz4Config() {
        return CompressionConfiguration.builder()
                .enabled(true)
                .backend(CompressionBackend.LZ4)
                .minCompressionSize(64)
                .build();
    }

    @BeforeAll
    @SneakyThrows
    public static void init() {
        standaloneClient =
                GlideClient.createClient(
                                commonClientConfig()
                                        .requestTimeout(10000)
                                        .compressionConfiguration(zstdConfig())
                                        .build())
                        .get();
        clusterClient =
                GlideClusterClient.createClient(
                                commonClusterClientConfig()
                                        .requestTimeout(10000)
                                        .compressionConfiguration(zstdConfig())
                                        .build())
                        .get();
        standaloneClientNoCompression =
                GlideClient.createClient(commonClientConfig().requestTimeout(10000).build()).get();
        clusterClientNoCompression =
                GlideClusterClient.createClient(commonClusterClientConfig().requestTimeout(10000).build())
                        .get();
        standaloneClientLz4 =
                GlideClient.createClient(
                                commonClientConfig()
                                        .requestTimeout(10000)
                                        .compressionConfiguration(lz4Config())
                                        .build())
                        .get();
    }

    @AfterAll
    @SneakyThrows
    public static void teardown() {
        standaloneClient.close();
        clusterClient.close();
        standaloneClientNoCompression.close();
        clusterClientNoCompression.close();
        standaloneClientLz4.close();
    }

    static Stream<Arguments> compressedClients() {
        return Stream.of(Arguments.of(standaloneClient), Arguments.of(clusterClient));
    }

    static Stream<Arguments> noCompressionClients() {
        return Stream.of(
                Arguments.of(standaloneClientNoCompression), Arguments.of(clusterClientNoCompression));
    }

    /** Generate a highly compressible string of the given size. */
    private static String compressibleText(int sizeBytes) {
        String pattern = "A".repeat(10) + "B".repeat(10) + "C".repeat(10);
        return pattern.repeat(sizeBytes / pattern.length() + 1).substring(0, sizeBytes);
    }

    private static long statLong(Map<String, String> stats, String key) {
        return Long.parseLong(stats.get(key));
    }

    // ==================== Basic SET/GET ====================

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("compressedClients")
    public void test_compression_basic_set_get(BaseClient client) {
        for (int size : new int[] {512, 1024, 10240, 102400}) {
            String key = "comp_basic_" + size + "_" + UUID.randomUUID();
            String value = compressibleText(size);

            Map<String, String> before = client.getStatistics();
            long beforeCompressed = statLong(before, "total_values_compressed");

            assertEquals(OK, client.set(key, value).get());
            assertEquals(value, client.get(key).get());

            Map<String, String> after = client.getStatistics();
            assertTrue(
                    statLong(after, "total_values_compressed") > beforeCompressed,
                    "Compression should be applied for " + size + "B value");

            // compressed bytes < original bytes (strict — test data is highly compressible)
            long origDelta =
                    statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
            long compDelta =
                    statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
            assertTrue(compDelta < origDelta, "Compressed size should be < original size");

            client.del(new String[] {key}).get();
        }
    }

    // ==================== Min-size threshold ====================

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("compressedClients")
    public void test_compression_min_size_threshold(BaseClient client) {
        // Below threshold — should be skipped
        for (int size : new int[] {32, 48, 63}) {
            String key = "below_" + size + "_" + UUID.randomUUID();
            String value = compressibleText(size);

            Map<String, String> before = client.getStatistics();
            long beforeSkipped = statLong(before, "compression_skipped_count");
            long beforeCompressed = statLong(before, "total_values_compressed");

            assertEquals(OK, client.set(key, value).get());
            assertEquals(value, client.get(key).get());

            Map<String, String> after = client.getStatistics();
            assertTrue(
                    statLong(after, "compression_skipped_count") > beforeSkipped,
                    "Compression should be skipped for " + size + "B value");
            assertEquals(
                    beforeCompressed,
                    statLong(after, "total_values_compressed"),
                    "No values should be compressed below threshold");

            client.del(new String[] {key}).get();
        }

        // At/above threshold — should be compressed
        for (int size : new int[] {64, 128, 256}) {
            String key = "above_" + size + "_" + UUID.randomUUID();
            String value = compressibleText(size);

            Map<String, String> before = client.getStatistics();
            long beforeCompressed = statLong(before, "total_values_compressed");

            assertEquals(OK, client.set(key, value).get());
            assertEquals(value, client.get(key).get());

            Map<String, String> after = client.getStatistics();
            assertTrue(
                    statLong(after, "total_values_compressed") > beforeCompressed,
                    "Compression should be applied for " + size + "B value");

            client.del(new String[] {key}).get();
        }
    }

    // ==================== Disabled by default ====================

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("noCompressionClients")
    public void test_compression_disabled_by_default(BaseClient client) {
        Map<String, String> before = client.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");
        long beforeSkipped = statLong(before, "compression_skipped_count");

        for (int size : new int[] {64, 1024, 10240}) {
            String key = "nocomp_" + size + "_" + UUID.randomUUID();
            String value = compressibleText(size);

            assertEquals(OK, client.set(key, value).get());
            assertEquals(value, client.get(key).get());
            client.del(new String[] {key}).get();
        }

        Map<String, String> after = client.getStatistics();
        assertEquals(
                beforeCompressed,
                statLong(after, "total_values_compressed"),
                "No compression when disabled");
        assertEquals(
                beforeSkipped,
                statLong(after, "compression_skipped_count"),
                "No compression attempts when disabled");
    }

    // ==================== LZ4 backend ====================

    @SneakyThrows
    @Test
    public void test_compression_lz4_backend() {
        String key = "lz4_test_" + UUID.randomUUID();
        String value = compressibleText(1024);

        Map<String, String> before = standaloneClientLz4.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");

        assertEquals(OK, standaloneClientLz4.set(key, value).get());
        assertEquals(value, standaloneClientLz4.get(key).get());

        Map<String, String> after = standaloneClientLz4.getStatistics();
        assertTrue(
                statLong(after, "total_values_compressed") > beforeCompressed,
                "LZ4 compression should be applied");

        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "LZ4 compressed size should be < original size");

        standaloneClientLz4.del(new String[] {key}).get();
    }

    // ==================== Cross-client interop ====================

    @SneakyThrows
    @Test
    public void test_compressed_value_readable_by_same_backend() {
        String key = "interop_" + UUID.randomUUID();
        String value = compressibleText(1024);

        // Write with compression
        assertEquals(OK, standaloneClient.set(key, value).get());
        // Read with same compression client
        assertEquals(value, standaloneClient.get(key).get());

        // Read with no-compression client — should get raw compressed bytes (not equal to original)
        String raw = standaloneClientNoCompression.get(key).get();
        assertNotNull(raw, "Key should exist — raw value must not be null");
        assertTrue(
                !value.equals(raw),
                "Non-compression client should not transparently decompress");

        standaloneClient.del(new String[] {key}).get();
    }

    // ==================== Cross-backend interop ====================

    @SneakyThrows
    @Test
    public void test_compression_backend_mismatch() {
        String key = "backend_mismatch_" + UUID.randomUUID();
        String value = compressibleText(10240); // 10KB

        // Write with ZSTD
        assertEquals(OK, standaloneClient.set(key, value).get());

        // Read with LZ4 — data should still be readable because decompression detects the header
        assertEquals(value, standaloneClientLz4.get(key).get());

        // Write with LZ4
        String key2 = "backend_mismatch2_" + UUID.randomUUID();
        assertEquals(OK, standaloneClientLz4.set(key2, value).get());

        // Read with ZSTD
        assertEquals(value, standaloneClient.get(key2).get());

        standaloneClient.del(new String[] {key, key2}).get();
    }

    // ==================== Empty value ====================

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("compressedClients")
    public void test_compression_empty_value(BaseClient client) {
        String key = "empty_" + UUID.randomUUID();

        Map<String, String> before = client.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");
        long beforeSkipped = statLong(before, "compression_skipped_count");

        assertEquals(OK, client.set(key, "").get());
        assertEquals("", client.get(key).get());

        Map<String, String> after = client.getStatistics();
        assertTrue(
                statLong(after, "compression_skipped_count") > beforeSkipped,
                "Empty value should be skipped");
        assertEquals(
                beforeCompressed,
                statLong(after, "total_values_compressed"),
                "Empty value should not be compressed");

        client.del(new String[] {key}).get();
    }

    // ==================== Very large value ====================

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("compressedClients")
    @Timeout(60)
    public void test_compression_very_large_value(BaseClient client) {
        String key = "very_large_" + UUID.randomUUID();
        int size = 10 * 1024 * 1024; // 10MB
        String value = compressibleText(size);

        Map<String, String> before = client.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        Map<String, String> after = client.getStatistics();
        assertTrue(
                statLong(after, "total_values_compressed") > beforeCompressed,
                "Compression should be applied for 10MB value");

        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "Compressed size should be < original size for 10MB value");

        client.del(new String[] {key}).get();
    }

    // ==================== TTL compatibility ====================

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("compressedClients")
    public void test_compression_with_ttl(BaseClient client) {
        String key = "ttl_test_" + UUID.randomUUID();
        String value = compressibleText(10240); // 10KB

        Map<String, String> before = client.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");

        assertEquals(OK, client.set(key, value).get());
        assertTrue(client.expire(key, 10).get(), "EXPIRE should succeed");

        // Verify value and TTL
        assertEquals(value, client.get(key).get());
        long ttl = client.ttl(key).get();
        assertTrue(ttl > 0 && ttl <= 10, "TTL should be between 1 and 10, got " + ttl);

        // Verify compression was applied
        Map<String, String> after = client.getStatistics();
        assertTrue(
                statLong(after, "total_values_compressed") > beforeCompressed,
                "Compression should be applied with TTL");

        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "Compressed size should be < original size with TTL");

        client.del(new String[] {key}).get();
    }

    // ==================== Batch operations ====================

    @SneakyThrows
    @Test
    public void test_compression_batch_standalone() {
        int numKeys = 20;
        String prefix = "batch_sa_" + UUID.randomUUID() + "_";

        Map<String, String> before = standaloneClient.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");

        Batch setBatch = new Batch();
        List<String> keys = new ArrayList<>();
        List<String> values = new ArrayList<>();
        for (int i = 0; i < numKeys; i++) {
            String key = prefix + i;
            String val = compressibleText(1024);
            keys.add(key);
            values.add(val);
            setBatch.set(key, val);
        }

        Object[] setResults = standaloneClient.exec(setBatch).get();
        for (Object r : setResults) {
            assertEquals(OK, r);
        }

        Map<String, String> after = standaloneClient.getStatistics();
        assertTrue(
                statLong(after, "total_values_compressed") - beforeCompressed >= numKeys,
                "All batch SET values should be compressed");

        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "Batch compressed size should be < original size");

        // Verify GET returns correct values
        Batch getBatch = new Batch();
        for (String key : keys) {
            getBatch.get(key);
        }
        Object[] getResults = standaloneClient.exec(getBatch).get();
        for (int i = 0; i < numKeys; i++) {
            assertEquals(values.get(i), getResults[i]);
        }

        // Cleanup
        standaloneClient.del(keys.toArray(new String[0])).get();
    }

    @SneakyThrows
    @Test
    public void test_compression_batch_cluster() {
        int numKeys = 20;
        String prefix = "batch_cl_" + UUID.randomUUID() + "_";

        Map<String, String> before = clusterClient.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");

        ClusterBatch setBatch = new ClusterBatch();
        List<String> keys = new ArrayList<>();
        List<String> values = new ArrayList<>();
        for (int i = 0; i < numKeys; i++) {
            String key = prefix + i;
            String val = compressibleText(1024);
            keys.add(key);
            values.add(val);
            setBatch.set(key, val);
        }

        Object[] setResults = clusterClient.exec(setBatch).get();
        for (Object r : setResults) {
            assertEquals(OK, r);
        }

        Map<String, String> after = clusterClient.getStatistics();
        assertTrue(
                statLong(after, "total_values_compressed") - beforeCompressed >= numKeys,
                "All batch SET values should be compressed");

        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "Cluster batch compressed size should be < original size");

        // Verify GET returns correct values
        ClusterBatch getBatch = new ClusterBatch();
        for (String key : keys) {
            getBatch.get(key);
        }
        Object[] getResults = clusterClient.exec(getBatch).get();
        for (int i = 0; i < numKeys; i++) {
            assertEquals(values.get(i), getResults[i]);
        }

        // Cleanup
        clusterClient.del(keys.toArray(new String[0])).get();
    }

    // ==================== Mixed-size batch ====================

    @SneakyThrows
    @Test
    public void test_compression_batch_mixed_sizes() {
        String prefix = "mixed_batch_" + UUID.randomUUID() + "_";

        Map<String, String> before = standaloneClient.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");
        long beforeSkipped = statLong(before, "compression_skipped_count");

        Batch batch = new Batch();
        List<String> keys = new ArrayList<>();
        List<String> values = new ArrayList<>();

        // 10 small values (below 64B threshold — should be skipped)
        for (int i = 0; i < 10; i++) {
            String key = prefix + "small_" + i;
            String val = compressibleText(32);
            keys.add(key);
            values.add(val);
            batch.set(key, val);
        }

        // 10 medium values (5KB — should be compressed)
        for (int i = 0; i < 10; i++) {
            String key = prefix + "medium_" + i;
            String val = compressibleText(5120);
            keys.add(key);
            values.add(val);
            batch.set(key, val);
        }

        // 10 large values (100KB — should be compressed)
        for (int i = 0; i < 10; i++) {
            String key = prefix + "large_" + i;
            String val = compressibleText(102400);
            keys.add(key);
            values.add(val);
            batch.set(key, val);
        }

        Object[] setResults = standaloneClient.exec(batch).get();
        for (Object r : setResults) {
            assertEquals(OK, r);
        }

        Map<String, String> after = standaloneClient.getStatistics();
        long skippedDelta = statLong(after, "compression_skipped_count") - beforeSkipped;
        long compressedDelta = statLong(after, "total_values_compressed") - beforeCompressed;

        assertEquals(10, skippedDelta, "10 small values should be skipped");
        assertEquals(20, compressedDelta, "20 medium+large values should be compressed");

        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "Mixed batch compressed size should be < original size");

        // Verify all values
        Batch getBatch = new Batch();
        for (String key : keys) {
            getBatch.get(key);
        }
        Object[] getResults = standaloneClient.exec(getBatch).get();
        for (int i = 0; i < keys.size(); i++) {
            assertEquals(values.get(i), getResults[i]);
        }

        standaloneClient.del(keys.toArray(new String[0])).get();
    }

    // ==================== Cluster multi-slot ====================

    @SneakyThrows
    @Test
    public void test_compression_cluster_multislot() {
        int numKeys = 100;
        String prefix = "multislot_" + UUID.randomUUID() + "_";

        Map<String, String> before = clusterClient.getStatistics();
        long beforeCompressed = statLong(before, "total_values_compressed");

        List<String> keys = new ArrayList<>();
        List<String> values = new ArrayList<>();
        for (int i = 0; i < numKeys; i++) {
            String key = prefix + i;
            String val = compressibleText(5120); // 5KB
            keys.add(key);
            values.add(val);
            assertEquals(OK, clusterClient.set(key, val).get());
        }

        Map<String, String> after = clusterClient.getStatistics();
        long compressedDelta = statLong(after, "total_values_compressed") - beforeCompressed;
        assertEquals(
                numKeys,
                compressedDelta,
                "All " + numKeys + " values should be compressed across slots");

        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "Multislot compressed size should be < original size");

        // Verify all values
        for (int i = 0; i < numKeys; i++) {
            assertEquals(values.get(i), clusterClient.get(keys.get(i)).get());
        }

        // Cleanup
        for (String key : keys) {
            clusterClient.del(new String[] {key}).get();
        }
    }

    // ==================== Configuration validation ====================

    @Test
    public void test_compression_config_validation_min_size_too_small() {
        assertThrows(
                ConfigurationError.class,
                () -> CompressionConfiguration.builder().enabled(true).minCompressionSize(1).build());
    }

    @Test
    public void test_compression_config_validation_min_size_boundary() {
        // Exactly at minimum allowed should succeed
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .minCompressionSize(CompressionConfiguration.MIN_ALLOWED_COMPRESSION_SIZE)
                        .build();
        assertEquals(
                CompressionConfiguration.MIN_ALLOWED_COMPRESSION_SIZE, config.getMinCompressionSize());
    }

    @Test
    public void test_compression_config_defaults() {
        CompressionConfiguration config = CompressionConfiguration.builder().build();
        assertEquals(false, config.isEnabled());
        assertEquals(CompressionBackend.ZSTD, config.getBackend());
        assertEquals(null, config.getCompressionLevel());
        assertEquals(64, config.getMinCompressionSize());
    }

    // ==================== Valid compression levels ====================

    static Stream<Arguments> validCompressionLevels() {
        return Stream.of(
                // ZSTD valid levels
                Arguments.of(CompressionBackend.ZSTD, 1),
                Arguments.of(CompressionBackend.ZSTD, 3),
                Arguments.of(CompressionBackend.ZSTD, 10),
                Arguments.of(CompressionBackend.ZSTD, 22),
                Arguments.of(CompressionBackend.ZSTD, -5),
                // LZ4 valid levels
                Arguments.of(CompressionBackend.LZ4, -128),
                Arguments.of(CompressionBackend.LZ4, -10),
                Arguments.of(CompressionBackend.LZ4, 0),
                Arguments.of(CompressionBackend.LZ4, 1),
                Arguments.of(CompressionBackend.LZ4, 6),
                Arguments.of(CompressionBackend.LZ4, 12));
    }

    @SneakyThrows
    @ParameterizedTest
    @MethodSource("validCompressionLevels")
    public void test_compression_valid_levels(CompressionBackend backend, int level) {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(backend)
                        .compressionLevel(level)
                        .minCompressionSize(64)
                        .build();

        try (GlideClient client =
                GlideClient.createClient(
                                commonClientConfig()
                                        .requestTimeout(10000)
                                        .compressionConfiguration(config)
                                        .build())
                        .get()) {
            String key = "level_" + backend + "_" + level + "_" + UUID.randomUUID();
            String value = compressibleText(1024);

            Map<String, String> before = client.getStatistics();
            long beforeCompressed = statLong(before, "total_values_compressed");

            assertEquals(OK, client.set(key, value).get());
            assertEquals(value, client.get(key).get());

            Map<String, String> after = client.getStatistics();
            assertTrue(
                    statLong(after, "total_values_compressed") > beforeCompressed,
                    "Compression should be applied for " + backend + " level " + level);

            long origDelta =
                    statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
            long compDelta =
                    statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
            assertTrue(
                    compDelta < origDelta,
                    "Compressed size should be < original for " + backend + " level " + level);

            client.del(new String[] {key}).get();
        }
    }

    // ==================== Invalid compression levels ====================

    static Stream<Arguments> invalidCompressionLevels() {
        return Stream.of(
                Arguments.of(CompressionBackend.ZSTD, 23), // Above max
                Arguments.of(CompressionBackend.ZSTD, 100),
                Arguments.of(CompressionBackend.ZSTD, -200000), // Below min
                Arguments.of(CompressionBackend.LZ4, 13), // Above max
                Arguments.of(CompressionBackend.LZ4, 100),
                Arguments.of(CompressionBackend.LZ4, -129), // Below min
                Arguments.of(CompressionBackend.LZ4, -1000));
    }

    @ParameterizedTest
    @MethodSource("invalidCompressionLevels")
    public void test_compression_invalid_levels(CompressionBackend backend, int level) {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(backend)
                        .compressionLevel(level)
                        .minCompressionSize(64)
                        .build();

        ExecutionException exception =
                assertThrows(
                        ExecutionException.class,
                        () ->
                                GlideClient.createClient(
                                                commonClientConfig()
                                                        .requestTimeout(10000)
                                                        .compressionConfiguration(config)
                                                        .build())
                                        .get());

        String errorMsg = exception.getCause().getMessage().toLowerCase();
        assertTrue(
                errorMsg.contains("compression") || errorMsg.contains("level"),
                "Error should mention compression level issue: " + exception.getCause().getMessage());
    }

    // ==================== Data types ====================

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("compressedClients")
    public void test_compression_various_data_types(BaseClient client) {
        Map<String, String> before = client.getStatistics();

        // JSON-like data
        String jsonKey = "json_" + UUID.randomUUID();
        String jsonValue =
                ("{\"id\":12345,\"name\":\"Test\",\"desc\":\"" + "A".repeat(200) + "\"}").repeat(10);
        assertEquals(OK, client.set(jsonKey, jsonValue).get());
        assertEquals(jsonValue, client.get(jsonKey).get());
        client.del(new String[] {jsonKey}).get();

        // XML-like data
        String xmlKey = "xml_" + UUID.randomUUID();
        String xmlValue =
                "<record><id>123</id><name>Test</name><value>Data</value></record>".repeat(20);
        assertEquals(OK, client.set(xmlKey, xmlValue).get());
        assertEquals(xmlValue, client.get(xmlKey).get());
        client.del(new String[] {xmlKey}).get();

        // Unicode data
        String unicodeKey = "unicode_" + UUID.randomUUID();
        String unicodeValue = "Hello世界🌍Привет مرحبا".repeat(50);
        assertEquals(OK, client.set(unicodeKey, unicodeValue).get());
        assertEquals(unicodeValue, client.get(unicodeKey).get());
        client.del(new String[] {unicodeKey}).get();

        Map<String, String> after = client.getStatistics();
        long origDelta =
                statLong(after, "total_original_bytes") - statLong(before, "total_original_bytes");
        long compDelta =
                statLong(after, "total_bytes_compressed") - statLong(before, "total_bytes_compressed");
        assertTrue(compDelta < origDelta, "Data types compressed size should be < original size");
    }
}
