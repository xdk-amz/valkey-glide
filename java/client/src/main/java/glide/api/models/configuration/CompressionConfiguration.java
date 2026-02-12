/** Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0 */
package glide.api.models.configuration;

import static connection_request.ConnectionRequestOuterClass.*;

import glide.api.models.exceptions.ConfigurationError;
import glide.internal.GlideNativeBridge;
import lombok.Builder;
import lombok.Getter;
import lombok.NonNull;

/**
 * Configuration for automatic compression of values.
 *
 * <p>When enabled, the client will automatically compress values for set-type commands and
 * decompress values for get-type commands. This can reduce bandwidth usage and storage
 * requirements.
 *
 * @example
 *     <pre>{@code
 * CompressionConfiguration compression =
 *     CompressionConfiguration.builder()
 *         .enabled(true)
 *         .backend(CompressionBackend.ZSTD)
 *         .compressionLevel(3)
 *         .minCompressionSize(64)
 *         .build();
 * }</pre>
 */
@Getter
@Builder(buildMethodName = "buildInternal")
public class CompressionConfiguration {

    /**
     * The minimum allowed value for {@code minCompressionSize}. This is fetched from the Rust core
     * via JNI to stay in sync with the compression header size (currently HEADER_SIZE + 1 = 6 bytes).
     */
    public static final int MIN_ALLOWED_COMPRESSION_SIZE =
            GlideNativeBridge.getMinCompressedSize();

    /** Whether compression is enabled. Defaults to {@code false}. */
    @Builder.Default private final boolean enabled = false;

    /** The compression backend to use. Defaults to {@link CompressionBackend#ZSTD}. */
    @NonNull @Builder.Default private final CompressionBackend backend = CompressionBackend.ZSTD;

    /**
     * The compression level to use. If {@code null}, the backend's default level will be used. Valid
     * ranges are backend-specific and validated by the Rust core. ZSTD default is 3, LZ4 default is
     * 0.
     */
    private final Integer compressionLevel;

    /**
     * The minimum size in bytes for values to be compressed. Values smaller than this will not be
     * compressed. Defaults to 64 bytes. Must be at least {@link #MIN_ALLOWED_COMPRESSION_SIZE}.
     */
    @Builder.Default private final int minCompressionSize = 64;

    /** Validates configuration and converts to protobuf format for the connection request. */
    public CompressionConfig toProtobuf() {
        validate();
        CompressionConfig.Builder builder =
                CompressionConfig.newBuilder()
                        .setEnabled(enabled)
                        .setBackend(
                                backend == CompressionBackend.LZ4
                                        ? connection_request.ConnectionRequestOuterClass.CompressionBackend.LZ4
                                        : connection_request.ConnectionRequestOuterClass.CompressionBackend.ZSTD)
                        .setMinCompressionSize(minCompressionSize);
        if (compressionLevel != null) {
            builder.setCompressionLevel(compressionLevel);
        }
        return builder.build();
    }

    /** Validates the configuration. Called at build time and before protobuf conversion. */
    void validate() {
        if (minCompressionSize < MIN_ALLOWED_COMPRESSION_SIZE) {
            throw new ConfigurationError(
                    "minCompressionSize must be at least " + MIN_ALLOWED_COMPRESSION_SIZE + " bytes");
        }
    }

    /**
     * Custom builder that validates configuration at build time. Delegates to Lombok's generated
     * builder for field handling, avoiding direct access to Lombok's internal field naming
     * conventions.
     */
    public static class CompressionConfigurationBuilder {
        public CompressionConfiguration build() {
            CompressionConfiguration config = buildInternal();
            config.validate();
            return config;
        }
    }
}
