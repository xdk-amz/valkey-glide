/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

public class CompressionConfigurationTest {

    @Test
    void builder_with_defaults() {
        CompressionConfiguration config = CompressionConfiguration.builder().build();

        assertFalse(config.isEnabled());
        assertEquals(CompressionBackend.ZSTD, config.getBackend());
        assertNull(config.getCompressionLevel());
        assertEquals(64, config.getMinCompressionSize());
    }

    @Test
    void builder_with_custom_values() {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.LZ4)
                        .compressionLevel(6)
                        .minCompressionSize(128)
                        .build();

        assertTrue(config.isEnabled());
        assertEquals(CompressionBackend.LZ4, config.getBackend());
        assertEquals(6, config.getCompressionLevel());
        assertEquals(128, config.getMinCompressionSize());
    }

    @Test
    void builder_with_zstd_backend() {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.ZSTD)
                        .compressionLevel(10)
                        .build();

        assertTrue(config.isEnabled());
        assertEquals(CompressionBackend.ZSTD, config.getBackend());
        assertEquals(10, config.getCompressionLevel());
    }

    @Test
    void builder_with_lz4_backend() {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.LZ4)
                        .compressionLevel(8)
                        .build();

        assertTrue(config.isEnabled());
        assertEquals(CompressionBackend.LZ4, config.getBackend());
        assertEquals(8, config.getCompressionLevel());
    }

    @Test
    void builder_with_null_compression_level() {
        CompressionConfiguration config =
                CompressionConfiguration.builder().enabled(true).compressionLevel(null).build();

        assertTrue(config.isEnabled());
        assertNull(config.getCompressionLevel());
    }

    @Test
    void builder_with_custom_min_size() {
        CompressionConfiguration config =
                CompressionConfiguration.builder().enabled(true).minCompressionSize(256).build();

        assertTrue(config.isEnabled());
        assertEquals(256, config.getMinCompressionSize());
    }

    @Test
    void toString_contains_all_fields() {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.LZ4)
                        .compressionLevel(5)
                        .minCompressionSize(100)
                        .build();

        String str = config.toString();
        assertTrue(str.contains("enabled=true"));
        assertTrue(str.contains("backend=LZ4"));
        assertTrue(str.contains("compressionLevel=5"));
        assertTrue(str.contains("minCompressionSize=100"));
    }

    @Test
    void builder_disabled_with_custom_settings() {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(false)
                        .backend(CompressionBackend.LZ4)
                        .compressionLevel(10)
                        .minCompressionSize(200)
                        .build();

        assertFalse(config.isEnabled());
        assertEquals(CompressionBackend.LZ4, config.getBackend());
        assertEquals(10, config.getCompressionLevel());
        assertEquals(200, config.getMinCompressionSize());
    }
}
