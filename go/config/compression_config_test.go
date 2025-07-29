// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

package config

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestCompressionConfig_DefaultConfiguration(t *testing.T) {
	config := NewCompressionConfig()

	assert.False(t, config.IsEnabled())
	assert.Equal(t, Zstd, config.GetBackend())
	assert.Nil(t, config.GetCompressionLevel())
	assert.Equal(t, 64, config.GetMinCompressionSize())
	assert.Nil(t, config.GetMaxCompressionSize())
}

func TestCompressionConfig_EnabledConfiguration(t *testing.T) {
	config := NewCompressionConfig().
		WithEnabled(true).
		WithBackend(Lz4).
		WithCompressionLevel(6).
		WithMinCompressionSize(128).
		WithMaxCompressionSize(1024)

	assert.True(t, config.IsEnabled())
	assert.Equal(t, Lz4, config.GetBackend())
	assert.Equal(t, 6, *config.GetCompressionLevel())
	assert.Equal(t, 128, config.GetMinCompressionSize())
	assert.Equal(t, 1024, *config.GetMaxCompressionSize())
}

func TestCompressionConfig_ValidZstdCompressionLevel(t *testing.T) {
	// Test valid ZSTD compression levels (1-22)
	config1 := NewCompressionConfig().WithBackend(Zstd).WithCompressionLevel(1)
	assert.NoError(t, config1.Validate())

	config22 := NewCompressionConfig().WithBackend(Zstd).WithCompressionLevel(22)
	assert.NoError(t, config22.Validate())

	config10 := NewCompressionConfig().WithBackend(Zstd).WithCompressionLevel(10)
	assert.NoError(t, config10.Validate())
}

func TestCompressionConfig_InvalidZstdCompressionLevel(t *testing.T) {
	// Test invalid ZSTD compression levels
	config0 := NewCompressionConfig().WithBackend(Zstd).WithCompressionLevel(0)
	err := config0.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "compressionLevel for ZSTD backend must be between 1 and 22")

	config23 := NewCompressionConfig().WithBackend(Zstd).WithCompressionLevel(23)
	err = config23.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "compressionLevel for ZSTD backend must be between 1 and 22")
}

func TestCompressionConfig_ValidLz4CompressionLevel(t *testing.T) {
	// Test valid LZ4 compression levels (1-12)
	config1 := NewCompressionConfig().WithBackend(Lz4).WithCompressionLevel(1)
	assert.NoError(t, config1.Validate())

	config12 := NewCompressionConfig().WithBackend(Lz4).WithCompressionLevel(12)
	assert.NoError(t, config12.Validate())

	config6 := NewCompressionConfig().WithBackend(Lz4).WithCompressionLevel(6)
	assert.NoError(t, config6.Validate())
}

func TestCompressionConfig_InvalidLz4CompressionLevel(t *testing.T) {
	// Test invalid LZ4 compression levels
	config0 := NewCompressionConfig().WithBackend(Lz4).WithCompressionLevel(0)
	err := config0.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "compressionLevel for LZ4 backend must be between 1 and 12")

	config13 := NewCompressionConfig().WithBackend(Lz4).WithCompressionLevel(13)
	err = config13.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "compressionLevel for LZ4 backend must be between 1 and 12")
}

func TestCompressionConfig_ValidMinCompressionSize(t *testing.T) {
	config0 := NewCompressionConfig().WithMinCompressionSize(0)
	assert.NoError(t, config0.Validate())

	config64 := NewCompressionConfig().WithMinCompressionSize(64)
	assert.NoError(t, config64.Validate())

	config1024 := NewCompressionConfig().WithMinCompressionSize(1024)
	assert.NoError(t, config1024.Validate())
}

func TestCompressionConfig_InvalidMinCompressionSize(t *testing.T) {
	config := NewCompressionConfig().WithMinCompressionSize(-1)
	err := config.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "minCompressionSize must be non-negative")
}

func TestCompressionConfig_ValidMaxCompressionSize(t *testing.T) {
	config1 := NewCompressionConfig().WithMinCompressionSize(64).WithMaxCompressionSize(128)
	assert.NoError(t, config1.Validate())

	config2 := NewCompressionConfig().WithMinCompressionSize(0).WithMaxCompressionSize(0)
	assert.NoError(t, config2.Validate())

	config3 := NewCompressionConfig().WithMinCompressionSize(100).WithMaxCompressionSize(100)
	assert.NoError(t, config3.Validate())
}

func TestCompressionConfig_InvalidMaxCompressionSize(t *testing.T) {
	// Test negative maxCompressionSize
	config1 := NewCompressionConfig().WithMaxCompressionSize(-1)
	err := config1.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "maxCompressionSize must be non-negative")

	// Test maxCompressionSize < minCompressionSize
	config2 := NewCompressionConfig().WithMinCompressionSize(128).WithMaxCompressionSize(64)
	err = config2.Validate()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "maxCompressionSize must be greater than or equal to minCompressionSize")
}

func TestCompressionConfig_NilCompressionLevel(t *testing.T) {
	// Test that nil compression level is valid (uses backend default)
	configZstd := NewCompressionConfig().WithBackend(Zstd)
	assert.NoError(t, configZstd.Validate())
	assert.Nil(t, configZstd.GetCompressionLevel())

	configLz4 := NewCompressionConfig().WithBackend(Lz4)
	assert.NoError(t, configLz4.Validate())
	assert.Nil(t, configLz4.GetCompressionLevel())
}

func TestCompressionConfig_NilMaxCompressionSize(t *testing.T) {
	// Test that nil maxCompressionSize is valid (no limit)
	config := NewCompressionConfig().WithMinCompressionSize(64)
	assert.NoError(t, config.Validate())
	assert.Nil(t, config.GetMaxCompressionSize())
}

func TestCompressionConfig_ComplexValidConfiguration(t *testing.T) {
	config := NewCompressionConfig().
		WithEnabled(true).
		WithBackend(Zstd).
		WithCompressionLevel(15).
		WithMinCompressionSize(32).
		WithMaxCompressionSize(2048)

	assert.NoError(t, config.Validate())
	assert.True(t, config.IsEnabled())
	assert.Equal(t, Zstd, config.GetBackend())
	assert.Equal(t, 15, *config.GetCompressionLevel())
	assert.Equal(t, 32, config.GetMinCompressionSize())
	assert.Equal(t, 2048, *config.GetMaxCompressionSize())
}

func TestCompressionConfig_ToProtobuf(t *testing.T) {
	config := NewCompressionConfig().
		WithEnabled(true).
		WithBackend(Lz4).
		WithCompressionLevel(8).
		WithMinCompressionSize(128).
		WithMaxCompressionSize(1024)

	proto := config.toProtobuf()

	assert.True(t, proto.Enabled)
	assert.Equal(t, uint32(8), *proto.CompressionLevel)
	assert.Equal(t, uint32(128), proto.MinCompressionSize)
	assert.Equal(t, uint32(1024), *proto.MaxCompressionSize)
}

func TestCompressionConfig_ToProtobufWithDefaults(t *testing.T) {
	config := NewCompressionConfig()
	proto := config.toProtobuf()

	assert.False(t, proto.Enabled)
	assert.Nil(t, proto.CompressionLevel)
	assert.Equal(t, uint32(64), proto.MinCompressionSize)
	assert.Nil(t, proto.MaxCompressionSize)
}

func TestClientConfiguration_WithCompression(t *testing.T) {
	compressionConfig := NewCompressionConfig().WithEnabled(true).WithBackend(Zstd)
	clientConfig := NewClientConfiguration().WithCompression(compressionConfig)

	// Verify compression is set
	assert.NotNil(t, clientConfig.compression)
	assert.True(t, clientConfig.compression.IsEnabled())
	assert.Equal(t, Zstd, clientConfig.compression.GetBackend())
}

func TestClusterClientConfiguration_WithCompression(t *testing.T) {
	compressionConfig := NewCompressionConfig().WithEnabled(true).WithBackend(Lz4)
	clusterConfig := NewClusterClientConfiguration().WithCompression(compressionConfig)

	// Verify compression is set
	assert.NotNil(t, clusterConfig.compression)
	assert.True(t, clusterConfig.compression.IsEnabled())
	assert.Equal(t, Lz4, clusterConfig.compression.GetBackend())
}

func TestClientConfiguration_ToProtobufWithCompression(t *testing.T) {
	compressionConfig := NewCompressionConfig().
		WithEnabled(true).
		WithBackend(Zstd).
		WithCompressionLevel(10)

	clientConfig := NewClientConfiguration().
		WithAddress(&NodeAddress{Host: "localhost", Port: 6379}).
		WithCompression(compressionConfig)

	proto, err := clientConfig.ToProtobuf()
	assert.NoError(t, err)
	assert.NotNil(t, proto.CompressionConfig)
	assert.True(t, proto.CompressionConfig.Enabled)
	assert.Equal(t, uint32(10), *proto.CompressionConfig.CompressionLevel)
}

func TestClusterClientConfiguration_ToProtobufWithCompression(t *testing.T) {
	compressionConfig := NewCompressionConfig().
		WithEnabled(true).
		WithBackend(Lz4).
		WithCompressionLevel(6)

	clusterConfig := NewClusterClientConfiguration().
		WithAddress(&NodeAddress{Host: "localhost", Port: 6379}).
		WithCompression(compressionConfig)

	proto, err := clusterConfig.ToProtobuf()
	assert.NoError(t, err)
	assert.NotNil(t, proto.CompressionConfig)
	assert.True(t, proto.CompressionConfig.Enabled)
	assert.Equal(t, uint32(6), *proto.CompressionConfig.CompressionLevel)
}

func TestClientConfiguration_ToProtobufWithInvalidCompression(t *testing.T) {
	// Create invalid compression config
	compressionConfig := NewCompressionConfig().
		WithEnabled(true).
		WithBackend(Zstd).
		WithCompressionLevel(25) // Invalid level for ZSTD

	clientConfig := NewClientConfiguration().
		WithAddress(&NodeAddress{Host: "localhost", Port: 6379}).
		WithCompression(compressionConfig)

	_, err := clientConfig.ToProtobuf()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "compression configuration validation failed")
	assert.Contains(t, err.Error(), "compressionLevel for ZSTD backend must be between 1 and 22")
}

func TestClusterClientConfiguration_ToProtobufWithInvalidCompression(t *testing.T) {
	// Create invalid compression config
	compressionConfig := NewCompressionConfig().
		WithEnabled(true).
		WithBackend(Lz4).
		WithCompressionLevel(15) // Invalid level for LZ4

	clusterConfig := NewClusterClientConfiguration().
		WithAddress(&NodeAddress{Host: "localhost", Port: 6379}).
		WithCompression(compressionConfig)

	_, err := clusterConfig.ToProtobuf()
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "compression configuration validation failed")
	assert.Contains(t, err.Error(), "compressionLevel for LZ4 backend must be between 1 and 12")
}
