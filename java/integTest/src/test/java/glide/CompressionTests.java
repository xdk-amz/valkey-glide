/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide;

import static glide.CompressionTestUtilities.createClientWithCompression;
import static glide.CompressionTestUtilities.createClientWithoutCompression;
import static glide.CompressionTestUtilities.generateBase64Data;
import static glide.CompressionTestUtilities.generateCompressibleText;
import static glide.CompressionTestUtilities.generateJsonData;
import static glide.CompressionTestUtilities.generateUnicodeText;
import static glide.CompressionTestUtilities.generateXmlData;
import static glide.TestUtilities.getRandomString;
import static glide.api.BaseClient.OK;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Named.named;

import glide.api.BaseClient;
import glide.api.models.configuration.CompressionBackend;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Stream;
import lombok.SneakyThrows;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

/** Integration tests for compression functionality. */
@Timeout(10)
public class CompressionTests {

    private static BaseClient standaloneClientZstd = null;
    private static BaseClient clusterClientZstd = null;
    private static BaseClient standaloneClientLz4 = null;
    private static BaseClient clusterClientLz4 = null;
    private static BaseClient standaloneClientNoCompression = null;
    private static BaseClient clusterClientNoCompression = null;

    @BeforeAll
    @SneakyThrows
    public static void init() {
        // Create clients with ZSTD compression
        standaloneClientZstd = createClientWithCompression(false, CompressionBackend.ZSTD, null);
        clusterClientZstd = createClientWithCompression(true, CompressionBackend.ZSTD, null);

        // Create clients with LZ4 compression
        standaloneClientLz4 = createClientWithCompression(false, CompressionBackend.LZ4, null);
        clusterClientLz4 = createClientWithCompression(true, CompressionBackend.LZ4, null);

        // Create clients without compression
        standaloneClientNoCompression = createClientWithoutCompression(false);
        clusterClientNoCompression = createClientWithoutCompression(true);
    }

    @AfterAll
    @SneakyThrows
    public static void teardown() {
        if (standaloneClientZstd != null) standaloneClientZstd.close();
        if (clusterClientZstd != null) clusterClientZstd.close();
        if (standaloneClientLz4 != null) standaloneClientLz4.close();
        if (clusterClientLz4 != null) clusterClientLz4.close();
        if (standaloneClientNoCompression != null) standaloneClientNoCompression.close();
        if (clusterClientNoCompression != null) clusterClientNoCompression.close();
    }

    public static Stream<Arguments> getClientsWithCompression() {
        return Stream.of(
                Arguments.of(named("Standalone-ZSTD", standaloneClientZstd)),
                Arguments.of(named("Cluster-ZSTD", clusterClientZstd)),
                Arguments.of(named("Standalone-LZ4", standaloneClientLz4)),
                Arguments.of(named("Cluster-LZ4", clusterClientLz4)));
    }

    public static Stream<Arguments> getClientsWithoutCompression() {
        return Stream.of(
                Arguments.of(named("Standalone-NoCompression", standaloneClientNoCompression)),
                Arguments.of(named("Cluster-NoCompression", clusterClientNoCompression)));
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_basic_set_get(BaseClient client) {
        // Test with various data sizes
        int[] sizes = {512, 1024, 10 * 1024, 100 * 1024};

        for (int size : sizes) {
            String key = getRandomString(10);
            String value = generateCompressibleText(size);

            // Set and get the value
            assertEquals(OK, client.set(key, value).get());
            String retrieved = client.get(key).get();
            assertEquals(value, retrieved);

            // Verify statistics show compression activity
            Map<String, String> stats = client.getStatistics();
            assertNotNull(stats);
            assertTrue(stats.containsKey("total_values_compressed"));
            assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
        }
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_min_size_threshold(BaseClient client) {
        // Test value below threshold (should be skipped)
        String smallKey = getRandomString(10);
        String smallValue = "small"; // < 64 bytes
        assertEquals(OK, client.set(smallKey, smallValue).get());
        assertEquals(smallValue, client.get(smallKey).get());

        // Test value at/above threshold (should be compressed)
        String largeKey = getRandomString(10);
        String largeValue = generateCompressibleText(1024); // > 64 bytes
        assertEquals(OK, client.set(largeKey, largeValue).get());
        assertEquals(largeValue, client.get(largeKey).get());

        // Verify statistics
        Map<String, String> stats = client.getStatistics();
        assertNotNull(stats);
        assertTrue(stats.containsKey("compression_skipped_count"));
        assertTrue(Long.parseLong(stats.get("compression_skipped_count")) > 0);
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithoutCompression")
    public void test_compression_disabled_by_default(BaseClient client) {
        String key = getRandomString(10);
        String value = generateCompressibleText(10 * 1024);

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        // Verify statistics show no compression activity
        Map<String, String> stats = client.getStatistics();
        assertNotNull(stats);
        assertTrue(stats.containsKey("total_values_compressed"));
        assertEquals("0", stats.get("total_values_compressed"));
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_compressible_text(BaseClient client) {
        String key = getRandomString(10);
        String value = generateCompressibleText(10 * 1024);

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        // Verify compression statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
        assertTrue(
                Long.parseLong(stats.get("total_bytes_compressed"))
                        < Long.parseLong(stats.get("total_original_bytes")));
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_json_data(BaseClient client) {
        String key = getRandomString(10);
        String value = generateJsonData(10 * 1024);

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        // Verify compression statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_xml_data(BaseClient client) {
        String key = getRandomString(10);
        String value = generateXmlData(10 * 1024);

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        // Verify compression statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_base64_data(BaseClient client) {
        String key = getRandomString(10);
        String value = generateBase64Data(10 * 1024);

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        // Verify compression statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_unicode_text(BaseClient client) {
        String key = getRandomString(10);
        String value = generateUnicodeText(10 * 1024);

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        // Verify compression statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_batch_set_get(BaseClient client) {
        int batchSize = 100;
        Map<String, String> keyValues = new HashMap<>();

        // Create batch of keys
        for (int i = 0; i < batchSize; i++) {
            String key = getRandomString(10) + "_" + i;
            String value = generateCompressibleText(5 * 1024);
            keyValues.put(key, value);
        }

        // Set all values
        for (Map.Entry<String, String> entry : keyValues.entrySet()) {
            assertEquals(OK, client.set(entry.getKey(), entry.getValue()).get());
        }

        // Get and verify all values
        for (Map.Entry<String, String> entry : keyValues.entrySet()) {
            assertEquals(entry.getValue(), client.get(entry.getKey()).get());
        }

        // Verify statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) >= batchSize);
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_batch_mixed_sizes(BaseClient client) {
        // Mix of small (< 64B), medium (5KB), large (100KB) values
        String smallKey = getRandomString(10) + "_small";
        String smallValue = "small"; // < 64 bytes

        String mediumKey = getRandomString(10) + "_medium";
        String mediumValue = generateCompressibleText(5 * 1024);

        String largeKey = getRandomString(10) + "_large";
        String largeValue = generateCompressibleText(100 * 1024);

        // Set all values
        assertEquals(OK, client.set(smallKey, smallValue).get());
        assertEquals(OK, client.set(mediumKey, mediumValue).get());
        assertEquals(OK, client.set(largeKey, largeValue).get());

        // Get and verify all values
        assertEquals(smallValue, client.get(smallKey).get());
        assertEquals(mediumValue, client.get(mediumKey).get());
        assertEquals(largeValue, client.get(largeKey).get());

        // Verify statistics show both compressed and skipped
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) >= 2); // medium and large
        assertTrue(Long.parseLong(stats.get("compression_skipped_count")) > 0); // small
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_empty_values(BaseClient client) {
        String key = getRandomString(10);
        String emptyValue = "";

        assertEquals(OK, client.set(key, emptyValue).get());
        assertEquals(emptyValue, client.get(key).get());

        // Empty values should be skipped
        Map<String, String> stats = client.getStatistics();
        assertTrue(stats.containsKey("compression_skipped_count"));
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_very_large_values(BaseClient client) {
        // Skip on macOS - resource limits
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("mac")) {
            return;
        }

        String key = getRandomString(10);
        String largeValue = generateCompressibleText(1024 * 1024); // 1MB

        assertEquals(OK, client.set(key, largeValue).get());
        assertEquals(largeValue, client.get(key).get());

        // Verify compression statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
        assertTrue(
                Long.parseLong(stats.get("total_bytes_compressed"))
                        < Long.parseLong(stats.get("total_original_bytes")));
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_special_characters(BaseClient client) {
        String key = getRandomString(10);
        String value = "Special chars: \n\t\r\\\"'`~!@#$%^&*()_+-=[]{}|;:,.<>?/\n".repeat(100);

        assertEquals(OK, client.set(key, value).get());
        assertEquals(value, client.get(key).get());

        // Verify compression statistics
        Map<String, String> stats = client.getStatistics();
        assertTrue(Long.parseLong(stats.get("total_values_compressed")) > 0);
    }

    @SneakyThrows
    @ParameterizedTest(autoCloseArguments = false)
    @MethodSource("getClientsWithCompression")
    public void test_compression_statistics_keys_present(BaseClient client) {
        // Verify all compression statistics keys are present
        Map<String, String> stats = client.getStatistics();

        assertTrue(stats.containsKey("total_values_compressed"));
        assertTrue(stats.containsKey("total_values_decompressed"));
        assertTrue(stats.containsKey("total_original_bytes"));
        assertTrue(stats.containsKey("total_bytes_compressed"));
        assertTrue(stats.containsKey("total_bytes_decompressed"));
        assertTrue(stats.containsKey("compression_skipped_count"));
    }
}
