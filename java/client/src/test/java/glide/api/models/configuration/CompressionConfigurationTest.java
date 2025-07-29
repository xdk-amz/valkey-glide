/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

import static org.junit.jupiter.api.Assertions.*;

import glide.api.models.exceptions.ConfigurationError;
import org.junit.jupiter.api.Test;

/** Unit tests for {@link CompressionConfiguration}. */
public class CompressionConfigurationTest {

    @Test
    public void testDefaultConfiguration() {
        CompressionConfiguration config = CompressionConfiguration.builder().build();

        assertFalse(config.isEnabled());
        assertEquals(CompressionBackend.ZSTD, config.getBackend());
        assertNull(config.getCompressionLevel());
        assertEquals(64, config.getMinCompressionSize());
        assertNull(config.getMaxCompressionSize());
    }

    @Test
    public void testEnabledConfiguration() {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.LZ4)
                        .compressionLevel(6)
                        .minCompressionSize(128)
                        .maxCompressionSize(1024)
                        .build();

        assertTrue(config.isEnabled());
        assertEquals(CompressionBackend.LZ4, config.getBackend());
        assertEquals(6, config.getCompressionLevel());
        assertEquals(128, config.getMinCompressionSize());
        assertEquals(1024, config.getMaxCompressionSize());
    }

    @Test
    public void testValidZstdCompressionLevel() {
        // Test valid ZSTD compression levels (1-22)
        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.ZSTD)
                                .compressionLevel(1)
                                .build());

        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.ZSTD)
                                .compressionLevel(22)
                                .build());

        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.ZSTD)
                                .compressionLevel(10)
                                .build());
    }

    @Test
    public void testInvalidZstdCompressionLevel() {
        // Test invalid ZSTD compression levels
        ConfigurationError exception1 =
                assertThrows(
                        ConfigurationError.class,
                        () -> {
                            CompressionConfiguration config = CompressionConfiguration.builder()
                                    .backend(CompressionBackend.ZSTD)
                                    .compressionLevel(0)
                                    .build();
                            config.validate();
                        });
        assertEquals(
                "compressionLevel for ZSTD backend must be between 1 and 22", exception1.getMessage());

        ConfigurationError exception2 =
                assertThrows(
                        ConfigurationError.class,
                        () -> {
                            CompressionConfiguration config = CompressionConfiguration.builder()
                                    .backend(CompressionBackend.ZSTD)
                                    .compressionLevel(23)
                                    .build();
                            config.validate();
                        });
        assertEquals(
                "compressionLevel for ZSTD backend must be between 1 and 22", exception2.getMessage());
    }

    @Test
    public void testValidLz4CompressionLevel() {
        // Test valid LZ4 compression levels (1-12)
        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.LZ4)
                                .compressionLevel(1)
                                .build());

        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.LZ4)
                                .compressionLevel(12)
                                .build());

        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.LZ4)
                                .compressionLevel(6)
                                .build());
    }

    @Test
    public void testInvalidLz4CompressionLevel() {
        // Test invalid LZ4 compression levels
        ConfigurationError exception1 =
                assertThrows(
                        ConfigurationError.class,
                        () -> {
                            CompressionConfiguration config = CompressionConfiguration.builder()
                                    .backend(CompressionBackend.LZ4)
                                    .compressionLevel(0)
                                    .build();
                            config.validate();
                        });
        assertEquals(
                "compressionLevel for LZ4 backend must be between 1 and 12", exception1.getMessage());

        ConfigurationError exception2 =
                assertThrows(
                        ConfigurationError.class,
                        () -> {
                            CompressionConfiguration config = CompressionConfiguration.builder()
                                    .backend(CompressionBackend.LZ4)
                                    .compressionLevel(13)
                                    .build();
                            config.validate();
                        });
        assertEquals(
                "compressionLevel for LZ4 backend must be between 1 and 12", exception2.getMessage());
    }

    @Test
    public void testValidMinCompressionSize() {
        assertDoesNotThrow(
                () -> CompressionConfiguration.builder().minCompressionSize(0).build());

        assertDoesNotThrow(
                () -> CompressionConfiguration.builder().minCompressionSize(64).build());

        assertDoesNotThrow(
                () -> CompressionConfiguration.builder().minCompressionSize(1024).build());
    }

    @Test
    public void testInvalidMinCompressionSize() {
        ConfigurationError exception =
                assertThrows(
                        ConfigurationError.class,
                        () -> {
                            CompressionConfiguration config = CompressionConfiguration.builder()
                                    .minCompressionSize(-1)
                                    .build();
                            config.validate();
                        });
        assertEquals("minCompressionSize must be non-negative", exception.getMessage());
    }

    @Test
    public void testValidMaxCompressionSize() {
        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .minCompressionSize(64)
                                .maxCompressionSize(128)
                                .build());

        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .minCompressionSize(0)
                                .maxCompressionSize(0)
                                .build());

        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .minCompressionSize(100)
                                .maxCompressionSize(100)
                                .build());
    }

    @Test
    public void testInvalidMaxCompressionSize() {
        // Test negative maxCompressionSize
        ConfigurationError exception1 =
                assertThrows(
                        ConfigurationError.class,
                        () -> {
                            CompressionConfiguration config = CompressionConfiguration.builder()
                                    .maxCompressionSize(-1)
                                    .build();
                            config.validate();
                        });
        assertEquals("maxCompressionSize must be non-negative", exception1.getMessage());

        // Test maxCompressionSize < minCompressionSize
        ConfigurationError exception2 =
                assertThrows(
                        ConfigurationError.class,
                        () -> {
                            CompressionConfiguration config = CompressionConfiguration.builder()
                                    .minCompressionSize(128)
                                    .maxCompressionSize(64)
                                    .build();
                            config.validate();
                        });
        assertEquals(
                "maxCompressionSize must be greater than or equal to minCompressionSize",
                exception2.getMessage());
    }

    @Test
    public void testNullCompressionLevel() {
        // Test that null compression level is valid (uses backend default)
        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.ZSTD)
                                .compressionLevel(null)
                                .build());

        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .backend(CompressionBackend.LZ4)
                                .compressionLevel(null)
                                .build());
    }

    @Test
    public void testNullMaxCompressionSize() {
        // Test that null maxCompressionSize is valid (no limit)
        assertDoesNotThrow(
                () ->
                        CompressionConfiguration.builder()
                                .minCompressionSize(64)
                                .maxCompressionSize(null)
                                .build());
    }

    @Test
    public void testComplexValidConfiguration() {
        CompressionConfiguration config =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.ZSTD)
                        .compressionLevel(15)
                        .minCompressionSize(32)
                        .maxCompressionSize(2048)
                        .build();

        assertTrue(config.isEnabled());
        assertEquals(CompressionBackend.ZSTD, config.getBackend());
        assertEquals(15, config.getCompressionLevel());
        assertEquals(32, config.getMinCompressionSize());
        assertEquals(2048, config.getMaxCompressionSize());
    }

    @Test
    public void testValidateMethodDirectly() {
        CompressionConfiguration validConfig = CompressionConfiguration.builder().build();
        assertDoesNotThrow(validConfig::validate);

        // Create an invalid config using builder and then validate
        CompressionConfiguration invalidConfig =
                CompressionConfiguration.builder()
                        .backend(CompressionBackend.ZSTD)
                        .compressionLevel(25) // Invalid compression level
                        .build();

        ConfigurationError exception = assertThrows(ConfigurationError.class, invalidConfig::validate);
        assertEquals(
                "compressionLevel for ZSTD backend must be between 1 and 22", exception.getMessage());
    }
}
