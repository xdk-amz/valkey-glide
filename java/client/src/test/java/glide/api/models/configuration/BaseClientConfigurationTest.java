/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

public class BaseClientConfigurationTest {

    /** Test implementation of BaseClientConfiguration for testing purposes */
    private static class TestClientConfiguration extends BaseClientConfiguration {
        private TestClientConfiguration(TestClientConfigurationBuilder builder) {
            super(builder);
        }

        public static TestClientConfigurationBuilder builder() {
            return new TestClientConfigurationBuilder();
        }

        @Override
        public BaseSubscriptionConfiguration getSubscriptionConfiguration() {
            return null;
        }

        public static class TestClientConfigurationBuilder
                extends BaseClientConfigurationBuilder<
                        TestClientConfiguration, TestClientConfigurationBuilder> {
            @Override
            protected TestClientConfigurationBuilder self() {
                return this;
            }

            @Override
            public TestClientConfiguration build() {
                return new TestClientConfiguration(this);
            }
        }
    }

    @Test
    public void testDatabaseIdDefault() {
        // Test that databaseId defaults to null when not specified
        TestClientConfiguration config = TestClientConfiguration.builder().build();
        assertNull(config.getDatabaseId());
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 5, 10, 15, 50, 100, 1000})
    public void testDatabaseIdValidRange(int databaseId) {
        // Test that non-negative database IDs are accepted (server-side validation will handle range
        // checks)
        TestClientConfiguration config =
                TestClientConfiguration.builder().databaseId(databaseId).build();
        assertEquals(databaseId, config.getDatabaseId());
    }

    @Test
    public void client_configuration_with_compression_enabled() {
        CompressionConfiguration compression =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.ZSTD)
                        .compressionLevel(5)
                        .minCompressionSize(100)
                        .build();

        TestClientConfiguration config =
                TestClientConfiguration.builder().compression(compression).build();

        assertEquals(compression, config.getCompression());
        assertEquals(true, config.getCompression().isEnabled());
        assertEquals(CompressionBackend.ZSTD, config.getCompression().getBackend());
        assertEquals(5, config.getCompression().getCompressionLevel());
        assertEquals(100, config.getCompression().getMinCompressionSize());
    }

    @Test
    public void client_configuration_with_compression_disabled() {
        CompressionConfiguration compression =
                CompressionConfiguration.builder().enabled(false).build();

        TestClientConfiguration config =
                TestClientConfiguration.builder().compression(compression).build();

        assertEquals(compression, config.getCompression());
        assertEquals(false, config.getCompression().isEnabled());
    }

    @Test
    public void client_configuration_without_compression() {
        TestClientConfiguration config = TestClientConfiguration.builder().build();

        assertNull(config.getCompression());
    }

    @Test
    public void client_configuration_compression_propagates_to_cluster() {
        CompressionConfiguration compression =
                CompressionConfiguration.builder()
                        .enabled(true)
                        .backend(CompressionBackend.LZ4)
                        .compressionLevel(8)
                        .build();

        // Test with GlideClusterClientConfiguration
        GlideClusterClientConfiguration clusterConfig =
                GlideClusterClientConfiguration.builder()
                        .address(NodeAddress.builder().host("localhost").port(6379).build())
                        .compression(compression)
                        .build();

        assertEquals(compression, clusterConfig.getCompression());
        assertEquals(true, clusterConfig.getCompression().isEnabled());
        assertEquals(CompressionBackend.LZ4, clusterConfig.getCompression().getBackend());
    }
}
