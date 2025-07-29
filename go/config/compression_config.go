// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

package config

import (
	"errors"
	"fmt"

	"github.com/valkey-io/valkey-glide/go/v2/internal/protobuf"
)

// CompressionBackend represents the compression backend to use for automatic compression.
type CompressionBackend int

const (
	// Zstd - Use zstd compression backend.
	//
	// Zstandard (zstd) is a fast compression algorithm that provides good compression ratios.
	// It supports compression levels from 1 to 22, where higher levels provide better compression
	// but slower speed.
	Zstd CompressionBackend = iota

	// Lz4 - Use lz4 compression backend.
	//
	// LZ4 is an extremely fast compression algorithm that prioritizes speed over compression
	// ratio. It supports compression levels from 1 to 12, where higher levels provide better
	// compression but slower speed.
	Lz4
)

func mapCompressionBackend(backend CompressionBackend) protobuf.CompressionBackend {
	if backend == Lz4 {
		return protobuf.CompressionBackend_LZ4
	}
	return protobuf.CompressionBackend_ZSTD
}

// CompressionConfig represents the compression configuration for automatic compression of values.
//
// This configuration enables transparent compression and decompression of values for set-type
// and get-type commands respectively. When enabled, values will be automatically compressed before
// being sent to the server and decompressed when received from the server.
//
// The compression is completely transparent to the application layer and maintains full backward
// compatibility with existing data and non-compression clients.
//
// Example usage:
//
//	compressionConfig := NewCompressionConfig().
//	    WithEnabled(true).
//	    WithBackend(Zstd).
//	    WithCompressionLevel(3).
//	    WithMinCompressionSize(64).
//	    WithMaxCompressionSize(1024 * 1024) // 1MB
type CompressionConfig struct {
	// Whether compression is enabled. Defaults to false.
	enabled bool

	// The compression backend to use. Defaults to Zstd.
	backend CompressionBackend

	// The compression level to use. If not set, the backend's default level will be used.
	//
	// Valid ranges:
	// - ZSTD: 1-22 (higher values provide better compression but slower speed)
	// - LZ4: 1-12 (higher values provide better compression but slower speed)
	//
	// Defaults to nil (uses backend default).
	compressionLevel *int

	// The minimum size in bytes for values to be compressed.
	// Values smaller than this will not be compressed to avoid overhead.
	// Defaults to 64 bytes.
	minCompressionSize int

	// The maximum size in bytes for values to be compressed.
	// Values larger than this will not be compressed.
	// If not set, no maximum limit is applied.
	// Defaults to nil (no limit).
	maxCompressionSize *int
}

// NewCompressionConfig returns a new CompressionConfig with default settings.
func NewCompressionConfig() *CompressionConfig {
	return &CompressionConfig{
		enabled:            false,
		backend:            Zstd,
		compressionLevel:   nil,
		minCompressionSize: 64,
		maxCompressionSize: nil,
	}
}

// WithEnabled sets whether compression is enabled.
func (config *CompressionConfig) WithEnabled(enabled bool) *CompressionConfig {
	config.enabled = enabled
	return config
}

// WithBackend sets the compression backend to use.
func (config *CompressionConfig) WithBackend(backend CompressionBackend) *CompressionConfig {
	config.backend = backend
	return config
}

// WithCompressionLevel sets the compression level to use.
// If not set, the backend's default level will be used.
//
// Valid ranges:
// - ZSTD: 1-22 (higher values provide better compression but slower speed)
// - LZ4: 1-12 (higher values provide better compression but slower speed)
func (config *CompressionConfig) WithCompressionLevel(level int) *CompressionConfig {
	config.compressionLevel = &level
	return config
}

// WithMinCompressionSize sets the minimum size in bytes for values to be compressed.
// Values smaller than this will not be compressed to avoid overhead.
func (config *CompressionConfig) WithMinCompressionSize(size int) *CompressionConfig {
	config.minCompressionSize = size
	return config
}

// WithMaxCompressionSize sets the maximum size in bytes for values to be compressed.
// Values larger than this will not be compressed.
// If not set, no maximum limit is applied.
func (config *CompressionConfig) WithMaxCompressionSize(size int) *CompressionConfig {
	config.maxCompressionSize = &size
	return config
}

// Validate validates the compression configuration parameters.
func (config *CompressionConfig) Validate() error {
	if config.minCompressionSize < 0 {
		return errors.New("minCompressionSize must be non-negative")
	}

	if config.maxCompressionSize != nil {
		if *config.maxCompressionSize < 0 {
			return errors.New("maxCompressionSize must be non-negative")
		}
		if *config.maxCompressionSize < config.minCompressionSize {
			return errors.New("maxCompressionSize must be greater than or equal to minCompressionSize")
		}
	}

	if config.compressionLevel != nil {
		// Validate compression level based on backend
		switch config.backend {
		case Zstd:
			if *config.compressionLevel < 1 || *config.compressionLevel > 22 {
				return errors.New("compressionLevel for ZSTD backend must be between 1 and 22")
			}
		case Lz4:
			if *config.compressionLevel < 1 || *config.compressionLevel > 12 {
				return errors.New("compressionLevel for LZ4 backend must be between 1 and 12")
			}
		default:
			return fmt.Errorf("unsupported compression backend: %v", config.backend)
		}
	}

	return nil
}

// toProtobuf converts the compression configuration to protobuf format.
func (config *CompressionConfig) toProtobuf() *protobuf.CompressionConfig {
	protoConfig := &protobuf.CompressionConfig{
		Enabled:            config.enabled,
		Backend:            mapCompressionBackend(config.backend),
		MinCompressionSize: uint32(config.minCompressionSize),
	}

	if config.compressionLevel != nil {
		level := uint32(*config.compressionLevel)
		protoConfig.CompressionLevel = &level
	}

	if config.maxCompressionSize != nil {
		maxSize := uint32(*config.maxCompressionSize)
		protoConfig.MaxCompressionSize = &maxSize
	}

	return protoConfig
}

// IsEnabled returns whether compression is enabled.
func (config *CompressionConfig) IsEnabled() bool {
	return config.enabled
}

// GetBackend returns the compression backend.
func (config *CompressionConfig) GetBackend() CompressionBackend {
	return config.backend
}

// GetCompressionLevel returns the compression level, or nil if not set.
func (config *CompressionConfig) GetCompressionLevel() *int {
	return config.compressionLevel
}

// GetMinCompressionSize returns the minimum compression size.
func (config *CompressionConfig) GetMinCompressionSize() int {
	return config.minCompressionSize
}

// GetMaxCompressionSize returns the maximum compression size, or nil if not set.
func (config *CompressionConfig) GetMaxCompressionSize() *int {
	return config.maxCompressionSize
}
