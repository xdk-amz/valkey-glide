/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide;

import static glide.TestUtilities.commonClientConfig;
import static glide.TestUtilities.commonClusterClientConfig;

import glide.api.BaseClient;
import glide.api.GlideClient;
import glide.api.GlideClusterClient;
import glide.api.models.configuration.CompressionBackend;
import glide.api.models.configuration.CompressionConfiguration;
import java.util.Base64;
import java.util.Random;
import java.util.concurrent.ExecutionException;
import lombok.experimental.UtilityClass;

/** Utility methods for compression integration tests. */
@UtilityClass
public class CompressionTestUtilities {

    private static final Random RANDOM = new Random();

    /**
     * Generates compressible text data of the specified size.
     *
     * @param sizeBytes Target size in bytes
     * @return Compressible text string
     */
    public static String generateCompressibleText(int sizeBytes) {
        StringBuilder sb = new StringBuilder(sizeBytes);
        String[] words = {
            "Lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
            "sed",
            "do",
            "eiusmod",
            "tempor",
            "incididunt",
            "ut",
            "labore",
            "et",
            "dolore"
        };

        while (sb.length() < sizeBytes) {
            sb.append(words[RANDOM.nextInt(words.length)]).append(" ");
        }

        return sb.substring(0, Math.min(sizeBytes, sb.length()));
    }

    /**
     * Generates JSON data of the specified size.
     *
     * @param sizeBytes Target size in bytes
     * @return JSON string
     */
    public static String generateJsonData(int sizeBytes) {
        StringBuilder sb = new StringBuilder(sizeBytes);
        sb.append("{");

        int fieldCount = 0;
        while (sb.length() < sizeBytes - 20) {
            if (fieldCount > 0) {
                sb.append(",");
            }
            sb.append("\"field").append(fieldCount).append("\":\"value").append(fieldCount).append("\"");
            fieldCount++;
        }

        sb.append("}");
        return sb.toString();
    }

    /**
     * Generates XML data of the specified size.
     *
     * @param sizeBytes Target size in bytes
     * @return XML string
     */
    public static String generateXmlData(int sizeBytes) {
        StringBuilder sb = new StringBuilder(sizeBytes);
        sb.append("<?xml version=\"1.0\"?><root>");

        int itemCount = 0;
        while (sb.length() < sizeBytes - 50) {
            sb.append("<item id=\"")
                    .append(itemCount)
                    .append("\">value")
                    .append(itemCount)
                    .append("</item>");
            itemCount++;
        }

        sb.append("</root>");
        return sb.toString();
    }

    /**
     * Generates Base64-encoded data of the specified size.
     *
     * @param sizeBytes Target size in bytes
     * @return Base64 string
     */
    public static String generateBase64Data(int sizeBytes) {
        byte[] data = new byte[sizeBytes * 3 / 4]; // Base64 expands by ~33%
        RANDOM.nextBytes(data);
        return Base64.getEncoder().encodeToString(data);
    }

    /**
     * Generates Unicode text data of the specified size.
     *
     * @param sizeBytes Target size in bytes
     * @return Unicode string
     */
    public static String generateUnicodeText(int sizeBytes) {
        StringBuilder sb = new StringBuilder(sizeBytes);
        String[] unicodeWords = {"Hello", "世界", "مرحبا", "Привет", "שלום", "こんにちは", "안녕하세요", "Γειά"};

        while (sb.length() < sizeBytes) {
            sb.append(unicodeWords[RANDOM.nextInt(unicodeWords.length)]).append(" ");
        }

        return sb.substring(0, Math.min(sizeBytes, sb.length()));
    }

    /**
     * Creates a client with compression enabled.
     *
     * @param clusterMode Whether to create a cluster client
     * @param backend Compression backend to use
     * @param level Compression level (null for default)
     * @return BaseClient with compression enabled
     */
    public static BaseClient createClientWithCompression(
            boolean clusterMode, CompressionBackend backend, Integer level)
            throws ExecutionException, InterruptedException {

        CompressionConfiguration compression =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(backend)
                        .compressionLevel(level)
                        .minCompressionSize(64)
                        .build();

        if (clusterMode) {
            return GlideClusterClient.createClient(
                            commonClusterClientConfig().compression(compression).requestTimeout(10000).build())
                    .get();
        } else {
            return GlideClient.createClient(
                            commonClientConfig().compression(compression).requestTimeout(10000).build())
                    .get();
        }
    }

    /**
     * Creates a client without compression.
     *
     * @param clusterMode Whether to create a cluster client
     * @return BaseClient without compression
     */
    public static BaseClient createClientWithoutCompression(boolean clusterMode)
            throws ExecutionException, InterruptedException {

        if (clusterMode) {
            return GlideClusterClient.createClient(
                            commonClusterClientConfig().requestTimeout(10000).build())
                    .get();
        } else {
            return GlideClient.createClient(commonClientConfig().requestTimeout(10000).build()).get();
        }
    }
}
