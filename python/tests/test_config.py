# Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

import pytest
from glide_shared.config import (
    AdvancedGlideClientConfiguration,
    AdvancedGlideClusterClientConfiguration,
    BackoffStrategy,
    BaseClientConfiguration,
    CompressionBackend,
    CompressionConfiguration,
    ConfigurationError,
    GlideClientConfiguration,
    GlideClusterClientConfiguration,
    NodeAddress,
    PeriodicChecksManualInterval,
    PeriodicChecksStatus,
    ReadFrom,
    TlsAdvancedConfiguration,
)
from glide_shared.protobuf.connection_request_pb2 import ConnectionRequest
from glide_shared.protobuf.connection_request_pb2 import ReadFrom as ProtobufReadFrom
from glide_shared.protobuf.connection_request_pb2 import TlsMode


def test_default_client_config():
    config = BaseClientConfiguration([])
    assert len(config.addresses) == 0
    assert config.read_from.value == ProtobufReadFrom.Primary
    assert config.use_tls is False
    assert config.client_name is None


def test_convert_to_protobuf():
    config = BaseClientConfiguration(
        [NodeAddress("127.0.0.1")],
        use_tls=True,
        read_from=ReadFrom.PREFER_REPLICA,
        client_name="TEST_CLIENT_NAME",
    )
    request = config._create_a_protobuf_conn_request()
    assert isinstance(request, ConnectionRequest)
    assert request.addresses[0].host == "127.0.0.1"
    assert request.addresses[0].port == 6379
    assert request.tls_mode is TlsMode.SecureTls
    assert request.read_from == ProtobufReadFrom.PreferReplica
    assert request.client_name == "TEST_CLIENT_NAME"


def test_periodic_checks_interval_to_protobuf():
    config = GlideClusterClientConfiguration(
        [NodeAddress("127.0.0.1")],
    )
    request = config._create_a_protobuf_conn_request(cluster_mode=True)
    assert not request.HasField("periodic_checks_disabled")
    assert not request.HasField("periodic_checks_manual_interval")

    config.periodic_checks = PeriodicChecksStatus.DISABLED
    request = config._create_a_protobuf_conn_request(cluster_mode=True)
    assert request.HasField("periodic_checks_disabled")

    config.periodic_checks = PeriodicChecksManualInterval(30)
    request = config._create_a_protobuf_conn_request(cluster_mode=True)
    assert request.periodic_checks_manual_interval.duration_in_sec == 30


def test_convert_config_with_azaffinity_to_protobuf():
    az = "us-east-1a"
    config = BaseClientConfiguration(
        [NodeAddress("127.0.0.1")],
        use_tls=True,
        read_from=ReadFrom.AZ_AFFINITY,
        client_az=az,
    )
    request = config._create_a_protobuf_conn_request()
    assert isinstance(request, ConnectionRequest)
    assert request.tls_mode is TlsMode.SecureTls
    assert request.read_from == ProtobufReadFrom.AZAffinity
    assert request.client_az == az


def test_convert_config_with_azaffinity_replicas_and_primary_to_protobuf():
    az = "us-east-1a"
    config = BaseClientConfiguration(
        [NodeAddress("127.0.0.1")],
        use_tls=True,
        read_from=ReadFrom.AZ_AFFINITY_REPLICAS_AND_PRIMARY,
        client_az=az,
    )
    request = config._create_a_protobuf_conn_request()
    assert isinstance(request, ConnectionRequest)
    assert request.tls_mode is TlsMode.SecureTls
    assert request.read_from == ProtobufReadFrom.AZAffinityReplicasAndPrimary
    assert request.client_az == az


def test_connection_timeout_in_protobuf_request():
    connection_timeout = 5000  # in milliseconds
    config = GlideClientConfiguration(
        [NodeAddress("127.0.0.1")],
        advanced_config=AdvancedGlideClientConfiguration(connection_timeout),
    )
    request = config._create_a_protobuf_conn_request()

    assert isinstance(request, ConnectionRequest)
    assert request.connection_timeout == connection_timeout

    config = GlideClusterClientConfiguration(
        [NodeAddress("127.0.0.1")],
        advanced_config=AdvancedGlideClusterClientConfiguration(connection_timeout),
    )
    request = config._create_a_protobuf_conn_request(cluster_mode=True)

    assert isinstance(request, ConnectionRequest)
    assert request.connection_timeout == connection_timeout


def test_reconnect_strategy_in_protobuf_request():
    reconnect_strategy = BackoffStrategy(7, 69, 3, 18)
    config = GlideClientConfiguration(
        [NodeAddress("127.0.0.1")],
        reconnect_strategy=reconnect_strategy,
    )
    request = config._create_a_protobuf_conn_request()

    assert isinstance(request, ConnectionRequest)
    assert (
        request.connection_retry_strategy.number_of_retries
        == reconnect_strategy.num_of_retries
    )
    assert request.connection_retry_strategy.factor == reconnect_strategy.factor
    assert (
        request.connection_retry_strategy.exponent_base
        == reconnect_strategy.exponent_base
    )
    assert (
        request.connection_retry_strategy.jitter_percent
        == reconnect_strategy.jitter_percent
    )

    config = GlideClusterClientConfiguration(
        [NodeAddress("127.0.0.1")],
        reconnect_strategy=reconnect_strategy,
    )
    request = config._create_a_protobuf_conn_request(cluster_mode=True)

    assert isinstance(request, ConnectionRequest)
    assert (
        request.connection_retry_strategy.number_of_retries
        == reconnect_strategy.num_of_retries
    )
    assert request.connection_retry_strategy.factor == reconnect_strategy.factor
    assert (
        request.connection_retry_strategy.exponent_base
        == reconnect_strategy.exponent_base
    )
    assert (
        request.connection_retry_strategy.jitter_percent
        == reconnect_strategy.jitter_percent
    )


def test_tls_insecure_in_protobuf_request():
    tls_conf = TlsAdvancedConfiguration(use_insecure_tls=True)

    config = GlideClientConfiguration(
        [NodeAddress("127.0.0.1")],
        use_tls=False,
        advanced_config=AdvancedGlideClientConfiguration(tls_config=tls_conf),
    )
    with pytest.raises(ConfigurationError):
        config._create_a_protobuf_conn_request()

    config = GlideClientConfiguration(
        [NodeAddress("127.0.0.1")],
        use_tls=True,
        advanced_config=AdvancedGlideClientConfiguration(tls_config=tls_conf),
    )
    request = config._create_a_protobuf_conn_request()

    assert isinstance(request, ConnectionRequest)
    assert request.tls_mode is TlsMode.InsecureTls

    config = GlideClusterClientConfiguration(
        [NodeAddress("127.0.0.1")],
        use_tls=False,
        advanced_config=AdvancedGlideClusterClientConfiguration(tls_config=tls_conf),
    )
    with pytest.raises(ConfigurationError):
        config._create_a_protobuf_conn_request(cluster_mode=True)

    config = GlideClusterClientConfiguration(
        [NodeAddress("127.0.0.1")],
        use_tls=True,
        advanced_config=AdvancedGlideClusterClientConfiguration(tls_config=tls_conf),
    )
    request = config._create_a_protobuf_conn_request(cluster_mode=True)

    assert isinstance(request, ConnectionRequest)
    assert request.tls_mode is TlsMode.InsecureTls


# Compression Configuration Tests

def test_compression_configuration_defaults():
    """Test CompressionConfiguration with default values."""
    config = CompressionConfiguration()
    assert config.enabled is False
    assert config.backend == CompressionBackend.ZSTD
    assert config.compression_level is None
    assert config.min_compression_size == 64
    assert config.max_compression_size is None


def test_compression_configuration_custom_values():
    """Test CompressionConfiguration with custom values."""
    config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.LZ4,
        compression_level=5,
        min_compression_size=128,
        max_compression_size=1024
    )
    assert config.enabled is True
    assert config.backend == CompressionBackend.LZ4
    assert config.compression_level == 5
    assert config.min_compression_size == 128
    assert config.max_compression_size == 1024


def test_compression_configuration_validation_min_size_negative():
    """Test validation fails for negative min_compression_size."""
    with pytest.raises(ConfigurationError, match="min_compression_size must be non-negative"):
        CompressionConfiguration(min_compression_size=-1)


def test_compression_configuration_validation_max_size_negative():
    """Test validation fails for negative max_compression_size."""
    with pytest.raises(ConfigurationError, match="max_compression_size must be non-negative"):
        CompressionConfiguration(max_compression_size=-1)


def test_compression_configuration_validation_max_less_than_min():
    """Test validation fails when max_compression_size < min_compression_size."""
    with pytest.raises(ConfigurationError, match="max_compression_size must be greater than or equal to min_compression_size"):
        CompressionConfiguration(min_compression_size=100, max_compression_size=50)


def test_compression_configuration_validation_zstd_level_invalid():
    """Test validation fails for invalid ZSTD compression level."""
    with pytest.raises(ConfigurationError, match="compression_level for ZSTD backend must be between 1 and 22"):
        CompressionConfiguration(backend=CompressionBackend.ZSTD, compression_level=0)
    
    with pytest.raises(ConfigurationError, match="compression_level for ZSTD backend must be between 1 and 22"):
        CompressionConfiguration(backend=CompressionBackend.ZSTD, compression_level=23)


def test_compression_configuration_validation_lz4_level_invalid():
    """Test validation fails for invalid LZ4 compression level."""
    with pytest.raises(ConfigurationError, match="compression_level for LZ4 backend must be between 1 and 12"):
        CompressionConfiguration(backend=CompressionBackend.LZ4, compression_level=0)
    
    with pytest.raises(ConfigurationError, match="compression_level for LZ4 backend must be between 1 and 12"):
        CompressionConfiguration(backend=CompressionBackend.LZ4, compression_level=13)


def test_compression_configuration_validation_valid_levels():
    """Test validation passes for valid compression levels."""
    # Valid ZSTD levels
    config = CompressionConfiguration(backend=CompressionBackend.ZSTD, compression_level=1)
    assert config.compression_level == 1
    
    config = CompressionConfiguration(backend=CompressionBackend.ZSTD, compression_level=22)
    assert config.compression_level == 22
    
    # Valid LZ4 levels
    config = CompressionConfiguration(backend=CompressionBackend.LZ4, compression_level=1)
    assert config.compression_level == 1
    
    config = CompressionConfiguration(backend=CompressionBackend.LZ4, compression_level=12)
    assert config.compression_level == 12


def test_compression_configuration_to_protobuf():
    """Test conversion of CompressionConfiguration to protobuf."""
    config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=10,
        min_compression_size=128,
        max_compression_size=2048
    )
    
    proto_config = config._to_protobuf()
    assert proto_config.enabled is True
    assert proto_config.backend == CompressionBackend.ZSTD.value
    assert proto_config.compression_level == 10
    assert proto_config.min_compression_size == 128
    assert proto_config.max_compression_size == 2048


def test_compression_configuration_to_protobuf_optional_fields():
    """Test conversion to protobuf with optional fields not set."""
    config = CompressionConfiguration(
        enabled=False,
        min_compression_size=64
    )
    
    proto_config = config._to_protobuf()
    assert proto_config.enabled is False
    assert proto_config.backend == CompressionBackend.ZSTD.value
    assert not proto_config.HasField("compression_level")
    assert proto_config.min_compression_size == 64
    assert not proto_config.HasField("max_compression_size")


def test_base_client_configuration_with_compression():
    """Test BaseClientConfiguration with compression configuration."""
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.LZ4,
        compression_level=5
    )
    
    config = BaseClientConfiguration(
        [NodeAddress("127.0.0.1")],
        compression=compression_config
    )
    
    assert config.compression == compression_config
    
    request = config._create_a_protobuf_conn_request()
    assert request.HasField("compression_config")
    assert request.compression_config.enabled is True
    assert request.compression_config.backend == CompressionBackend.LZ4.value
    assert request.compression_config.compression_level == 5


def test_base_client_configuration_without_compression():
    """Test BaseClientConfiguration without compression configuration."""
    config = BaseClientConfiguration([NodeAddress("127.0.0.1")])
    
    assert config.compression is None
    
    request = config._create_a_protobuf_conn_request()
    assert not request.HasField("compression_config")


def test_glide_client_configuration_with_compression():
    """Test GlideClientConfiguration with compression configuration."""
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.ZSTD,
        compression_level=15,
        min_compression_size=256
    )
    
    config = GlideClientConfiguration(
        [NodeAddress("127.0.0.1")],
        compression=compression_config
    )
    
    assert config.compression == compression_config
    
    request = config._create_a_protobuf_conn_request()
    assert request.HasField("compression_config")
    assert request.compression_config.enabled is True
    assert request.compression_config.backend == CompressionBackend.ZSTD.value
    assert request.compression_config.compression_level == 15
    assert request.compression_config.min_compression_size == 256


def test_glide_cluster_client_configuration_with_compression():
    """Test GlideClusterClientConfiguration with compression configuration."""
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=CompressionBackend.LZ4,
        min_compression_size=512,
        max_compression_size=4096
    )
    
    config = GlideClusterClientConfiguration(
        [NodeAddress("127.0.0.1")],
        compression=compression_config
    )
    
    assert config.compression == compression_config
    
    request = config._create_a_protobuf_conn_request(cluster_mode=True)
    assert request.HasField("compression_config")
    assert request.compression_config.enabled is True
    assert request.compression_config.backend == CompressionBackend.LZ4.value
    assert not request.compression_config.HasField("compression_level")
    assert request.compression_config.min_compression_size == 512
    assert request.compression_config.max_compression_size == 4096


def test_compression_backend_enum_values():
    """Test CompressionBackend enum values match protobuf values."""
    from glide.protobuf.connection_request_pb2 import CompressionBackend as ProtobufCompressionBackend
    
    assert CompressionBackend.ZSTD.value == ProtobufCompressionBackend.ZSTD
    assert CompressionBackend.LZ4.value == ProtobufCompressionBackend.LZ4
