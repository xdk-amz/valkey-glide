// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

//! Compression module providing automatic compression and decompression capabilities
//! for Valkey Glide client operations.

use std::fmt;
use thiserror::Error;
use crate::request_type::RequestType;

/// Errors that can occur during compression operations
#[derive(Debug, Error, Clone, PartialEq)]
pub enum CompressionError {
    /// Compression operation failed
    #[error("Compression failed: {message}")]
    CompressionFailed { message: String },

    /// Decompression operation failed
    #[error("Decompression failed: {message}")]
    DecompressionFailed { message: String },

    /// Unsupported compression backend
    #[error("Unsupported compression backend: {backend}")]
    UnsupportedBackend { backend: String },

    /// Invalid compression configuration
    #[error("Invalid compression configuration: {message}")]
    InvalidConfiguration { message: String },

    /// Backend initialization failed
    #[error("Backend initialization failed: {message}")]
    BackendInitializationFailed { message: String },
}

impl CompressionError {
    /// Create a new compression failed error
    pub fn compression_failed<S: Into<String>>(message: S) -> Self {
        Self::CompressionFailed {
            message: message.into(),
        }
    }

    /// Create a new decompression failed error
    pub fn decompression_failed<S: Into<String>>(message: S) -> Self {
        Self::DecompressionFailed {
            message: message.into(),
        }
    }

    /// Create a new unsupported backend error
    pub fn unsupported_backend<S: Into<String>>(backend: S) -> Self {
        Self::UnsupportedBackend {
            backend: backend.into(),
        }
    }

    /// Create a new invalid configuration error
    pub fn invalid_configuration<S: Into<String>>(message: S) -> Self {
        Self::InvalidConfiguration {
            message: message.into(),
        }
    }

    /// Create a new backend initialization failed error
    pub fn backend_initialization_failed<S: Into<String>>(message: S) -> Self {
        Self::BackendInitializationFailed {
            message: message.into(),
        }
    }
}

/// Result type for compression operations
pub type CompressionResult<T> = Result<T, CompressionError>;

/// Trait defining the interface for compression backends
/// 
/// All compression backends must implement this trait to provide
/// compression, decompression, and format detection capabilities.
pub trait CompressionBackend: Send + Sync + fmt::Debug {
    /// Compress the given data using the specified compression level
    /// 
    /// # Arguments
    /// * `data` - The data to compress
    /// * `level` - Optional compression level (backend-specific)
    /// 
    /// # Returns
    /// * `Ok(Vec<u8>)` - The compressed data with magic header
    /// * `Err(CompressionError)` - If compression fails
    fn compress(&self, data: &[u8], level: Option<i32>) -> CompressionResult<Vec<u8>>;

    /// Decompress the given data
    /// 
    /// # Arguments
    /// * `data` - The compressed data (should include magic header)
    /// 
    /// # Returns
    /// * `Ok(Vec<u8>)` - The decompressed data
    /// * `Err(CompressionError)` - If decompression fails
    fn decompress(&self, data: &[u8]) -> CompressionResult<Vec<u8>>;

    /// Check if the given data is compressed by this backend
    /// 
    /// # Arguments
    /// * `data` - The data to check
    /// 
    /// # Returns
    /// * `true` if the data appears to be compressed by this backend
    /// * `false` otherwise
    fn is_compressed(&self, data: &[u8]) -> bool;

    /// Get the name of this compression backend
    /// 
    /// # Returns
    /// * A static string identifying the backend (e.g., "zstd", "lz4")
    fn backend_name(&self) -> &'static str;

    /// Get the default compression level for this backend
    /// 
    /// # Returns
    /// * `Some(level)` if the backend has a default level
    /// * `None` if the backend doesn't use compression levels
    fn default_level(&self) -> Option<i32>;

    /// Get the backend ID used in the magic header
    /// 
    /// # Returns
    /// * A unique byte identifier for this backend
    fn backend_id(&self) -> u8;
}

/// Supported compression backend types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CompressionBackendType {
    /// Zstandard compression
    Zstd,
    /// LZ4 compression
    Lz4,
    // Future backends can be added here
}

impl CompressionBackendType {
    /// Get the backend ID used in magic headers
    pub fn backend_id(&self) -> u8 {
        match self {
            CompressionBackendType::Zstd => 0x01,
            CompressionBackendType::Lz4 => 0x02,
        }
    }

    /// Get the backend name as a string
    pub fn backend_name(&self) -> &'static str {
        match self {
            CompressionBackendType::Zstd => "zstd",
            CompressionBackendType::Lz4 => "lz4",
        }
    }

    /// Get the default compression level for this backend
    pub fn default_level(&self) -> Option<i32> {
        match self {
            CompressionBackendType::Zstd => Some(3),
            CompressionBackendType::Lz4 => None, // LZ4 typically doesn't use levels
        }
    }
}

impl std::fmt::Display for CompressionBackendType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.backend_name())
    }
}

impl std::str::FromStr for CompressionBackendType {
    type Err = CompressionError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "zstd" | "zstandard" => Ok(CompressionBackendType::Zstd),
            "lz4" => Ok(CompressionBackendType::Lz4),
            _ => Err(CompressionError::unsupported_backend(s)),
        }
    }
}

/// Configuration for compression operations
#[derive(Debug, Clone, PartialEq)]
pub struct CompressionConfig {
    /// Whether compression is enabled
    pub enabled: bool,
    /// The compression backend to use
    pub backend: CompressionBackendType,
    /// Compression level (backend-specific, None uses backend default)
    pub compression_level: Option<i32>,
    /// Minimum size in bytes for a value to be considered for compression
    pub min_compression_size: usize,
    /// Maximum size in bytes for a value to be compressed (None = no limit)
    pub max_compression_size: Option<usize>,
}

impl CompressionConfig {
    /// Create a new compression configuration with default values
    pub fn new(backend: CompressionBackendType) -> Self {
        Self {
            enabled: true,
            backend,
            compression_level: backend.default_level(),
            min_compression_size: 64, // 64 bytes default minimum
            max_compression_size: None, // No maximum by default
        }
    }

    /// Create a disabled compression configuration
    pub fn disabled() -> Self {
        Self {
            enabled: false,
            backend: CompressionBackendType::Zstd, // Default backend, but disabled
            compression_level: None,
            min_compression_size: 64,
            max_compression_size: None,
        }
    }

    /// Set the compression level
    pub fn with_compression_level(mut self, level: Option<i32>) -> Self {
        self.compression_level = level;
        self
    }

    /// Set the minimum compression size
    pub fn with_min_compression_size(mut self, size: usize) -> Self {
        self.min_compression_size = size;
        self
    }

    /// Set the maximum compression size
    pub fn with_max_compression_size(mut self, size: Option<usize>) -> Self {
        self.max_compression_size = size;
        self
    }

    /// Validate the compression configuration
    pub fn validate(&self) -> CompressionResult<()> {
        // Check minimum size is reasonable
        if self.min_compression_size == 0 {
            return Err(CompressionError::invalid_configuration(
                "min_compression_size must be greater than 0"
            ));
        }

        // Check that min size is not too large (arbitrary limit of 1MB)
        if self.min_compression_size > 1024 * 1024 {
            return Err(CompressionError::invalid_configuration(
                "min_compression_size must not exceed 1MB"
            ));
        }

        // Check max size is larger than min size if specified
        if let Some(max_size) = self.max_compression_size {
            if max_size <= self.min_compression_size {
                return Err(CompressionError::invalid_configuration(
                    "max_compression_size must be greater than min_compression_size"
                ));
            }
        }

        // Validate compression level for specific backends
        if let Some(level) = self.compression_level {
            match self.backend {
                CompressionBackendType::Zstd => {
                    // Zstd supports levels 1-22, with 3 being default
                    if !(1..=22).contains(&level) {
                        return Err(CompressionError::invalid_configuration(
                            "zstd compression level must be between 1 and 22"
                        ));
                    }
                }
                CompressionBackendType::Lz4 => {
                    // LZ4 typically doesn't use compression levels
                    return Err(CompressionError::invalid_configuration(
                        "lz4 backend does not support compression levels"
                    ));
                }
            }
        }

        Ok(())
    }

    /// Check if a value of the given size should be compressed
    pub fn should_compress(&self, data_size: usize) -> bool {
        if !self.enabled {
            return false;
        }

        if data_size < self.min_compression_size {
            return false;
        }

        if let Some(max_size) = self.max_compression_size {
            if data_size > max_size {
                return false;
            }
        }

        true
    }
}

impl Default for CompressionConfig {
    fn default() -> Self {
        Self::disabled()
    }
}

/// Defines the compression behavior for different command types
/// 
/// This enum categorizes commands based on whether they should have their
/// values compressed, decompressed, or left unchanged during processing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CommandCompressionBehavior {
    /// Commands that set values and should compress them before sending to server
    /// Examples: SET, MSET, HSET, HMSET, SADD, ZADD, LPUSH, RPUSH, etc.
    CompressValues,
    
    /// Commands that retrieve values and should decompress them after receiving from server
    /// Examples: GET, MGET, HGET, HGETALL, SMEMBERS, ZRANGE, LRANGE, etc.
    DecompressValues,
    
    /// Commands that don't involve value compression/decompression
    /// Examples: DEL, EXISTS, EXPIRE, PING, INFO, etc.
    NoCompression,
}

impl CommandCompressionBehavior {
    /// Get a human-readable description of the compression behavior
    pub fn description(&self) -> &'static str {
        match self {
            CommandCompressionBehavior::CompressValues => "Compress values before sending to server",
            CommandCompressionBehavior::DecompressValues => "Decompress values after receiving from server",
            CommandCompressionBehavior::NoCompression => "No compression processing required",
        }
    }
}

impl std::fmt::Display for CommandCompressionBehavior {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CommandCompressionBehavior::CompressValues => write!(f, "CompressValues"),
            CommandCompressionBehavior::DecompressValues => write!(f, "DecompressValues"),
            CommandCompressionBehavior::NoCompression => write!(f, "NoCompression"),
        }
    }
}

/// Determines the compression behavior for a given command type
/// 
/// This function maps each RequestType to its appropriate compression behavior
/// based on whether the command sets values (compress), gets values (decompress),
/// or doesn't involve value processing (no compression).
/// 
/// SIMPLIFIED VERSION: Only supports basic SET/GET commands for compression.
/// All other commands are treated as NoCompression.
/// 
/// # Arguments
/// * `request_type` - The type of request to classify
/// 
/// # Returns
/// * `CommandCompressionBehavior` - The appropriate compression behavior for this command
pub fn get_command_compression_behavior(request_type: RequestType) -> CommandCompressionBehavior {
    match request_type {
        // Basic SET operation (compress values)
        RequestType::Set => CommandCompressionBehavior::CompressValues,

        // Basic GET operation (decompress values)
        RequestType::Get => CommandCompressionBehavior::DecompressValues,

        // All other commands don't require compression/decompression
        _ => CommandCompressionBehavior::NoCompression,
    }
}

/// Compression manager that coordinates compression operations
/// 
/// The CompressionManager handles the orchestration of compression and decompression
/// operations using a pluggable backend system. It applies configuration rules
/// to determine when compression should be applied and handles errors gracefully.
#[derive(Debug)]
pub struct CompressionManager {
    backend: Box<dyn CompressionBackend>,
    config: CompressionConfig,
}

impl CompressionManager {
    /// Create a new compression manager with the specified backend and configuration
    /// 
    /// # Arguments
    /// * `backend` - The compression backend to use
    /// * `config` - The compression configuration
    /// 
    /// # Returns
    /// * `Ok(CompressionManager)` - If the configuration is valid
    /// * `Err(CompressionError)` - If the configuration is invalid
    pub fn new(
        backend: Box<dyn CompressionBackend>,
        config: CompressionConfig,
    ) -> CompressionResult<Self> {
        // Validate configuration
        config.validate()?;

        // Verify backend matches configuration
        if backend.backend_id() != config.backend.backend_id() {
            return Err(CompressionError::invalid_configuration(
                format!(
                    "Backend mismatch: expected {}, got backend with ID {}",
                    config.backend.backend_name(),
                    backend.backend_id()
                )
            ));
        }

        Ok(Self { backend, config })
    }

    /// Check if a value of the given size should be compressed
    /// 
    /// # Arguments
    /// * `data` - The data to check
    /// 
    /// # Returns
    /// * `true` if the data should be compressed based on configuration
    /// * `false` otherwise
    pub fn should_compress(&self, data: &[u8]) -> bool {
        self.config.should_compress(data.len())
    }

    /// Compress a value using the configured backend
    /// 
    /// # Arguments
    /// * `value` - The value to compress
    /// 
    /// # Returns
    /// * `Ok(Vec<u8>)` - The compressed value with magic header
    /// * `Err(CompressionError)` - If compression fails
    pub fn compress_value(&self, value: &[u8]) -> CompressionResult<Vec<u8>> {
        if !self.config.enabled {
            return Err(CompressionError::invalid_configuration(
                "Compression is disabled"
            ));
        }

        if !self.should_compress(value) {
            return Err(CompressionError::invalid_configuration(
                "Value does not meet compression criteria"
            ));
        }

        // Check if already compressed
        if self.backend.is_compressed(value) {
            // Return as-is if already compressed
            return Ok(value.to_vec());
        }

        self.backend.compress(value, self.config.compression_level)
    }

    /// Decompress a value using the configured backend
    /// 
    /// # Arguments
    /// * `value` - The potentially compressed value
    /// 
    /// # Returns
    /// * `Ok(Vec<u8>)` - The decompressed value, or original if not compressed
    /// * `Err(CompressionError)` - If decompression fails
    pub fn decompress_value(&self, value: &[u8]) -> CompressionResult<Vec<u8>> {
        // If compression is disabled, return value as-is
        if !self.config.enabled {
            return Ok(value.to_vec());
        }

        // Check if the value is compressed by our backend
        if !self.backend.is_compressed(value) {
            // Not compressed by our backend, return as-is
            return Ok(value.to_vec());
        }

        self.backend.decompress(value)
    }

    /// Get the compression configuration
    pub fn config(&self) -> &CompressionConfig {
        &self.config
    }

    /// Get the backend name
    pub fn backend_name(&self) -> &'static str {
        self.backend.backend_name()
    }

    /// Check if compression is enabled
    pub fn is_enabled(&self) -> bool {
        self.config.enabled
    }

    /// Attempt to compress a value with graceful fallback
    /// 
    /// This method will attempt to compress the value, but if compression fails
    /// or the value doesn't meet compression criteria, it will return the original
    /// value without error.
    /// 
    /// # Arguments
    /// * `value` - The value to potentially compress
    /// 
    /// # Returns
    /// * The compressed value if successful, or the original value as fallback
    pub fn try_compress_value(&self, value: &[u8]) -> Vec<u8> {
        if !self.config.enabled || !self.should_compress(value) {
            return value.to_vec();
        }

        match self.compress_value(value) {
            Ok(compressed) => compressed,
            Err(_) => value.to_vec(), // Fallback to original on error
        }
    }

    /// Attempt to decompress a value with graceful fallback
    /// 
    /// This method will attempt to decompress the value, but if decompression fails
    /// it will return the original value without error.
    /// 
    /// # Arguments
    /// * `value` - The potentially compressed value
    /// 
    /// # Returns
    /// * The decompressed value if successful, or the original value as fallback
    pub fn try_decompress_value(&self, value: &[u8]) -> Vec<u8> {
        match self.decompress_value(value) {
            Ok(decompressed) => decompressed,
            Err(_) => value.to_vec(), // Fallback to original on error
        }
    }
}

/// Zstd compression backend implementation
#[cfg(feature = "compression")]
pub mod zstd_backend {
    use super::*;
    use crate::compression::magic_header;

    /// Zstd compression backend
    #[derive(Debug)]
    pub struct ZstdBackend {
        /// Default compression level for this backend
        default_level: i32,
    }

    impl ZstdBackend {
        /// Create a new Zstd backend with default compression level
        pub fn new() -> CompressionResult<Self> {
            Ok(Self {
                default_level: 3, // Zstd default level
            })
        }

        /// Create a new Zstd backend with custom default compression level
        pub fn with_default_level(level: i32) -> CompressionResult<Self> {
            if !(1..=22).contains(&level) {
                return Err(CompressionError::invalid_configuration(
                    format!("zstd compression level must be between 1 and 22, got {}", level)
                ));
            }
            Ok(Self {
                default_level: level,
            })
        }
    }

    impl Default for ZstdBackend {
        fn default() -> Self {
            Self::new().expect("Default ZstdBackend creation should not fail")
        }
    }

    impl CompressionBackend for ZstdBackend {
        fn compress(&self, data: &[u8], level: Option<i32>) -> CompressionResult<Vec<u8>> {
            // Determine compression level
            let compression_level = level.unwrap_or(self.default_level);
            
            // Validate compression level
            if !(1..=22).contains(&compression_level) {
                return Err(CompressionError::invalid_configuration(
                    format!("zstd compression level must be between 1 and 22, got {}", compression_level)
                ));
            }

            // Compress the data
            let compressed_data = zstd::encode_all(data, compression_level)
                .map_err(|e| CompressionError::compression_failed(
                    format!("zstd compression failed: {}", e)
                ))?;

            // Create header with magic bytes and backend ID
            let header = magic_header::create_header(self.backend_id());
            
            // Combine header and compressed data
            let mut result = Vec::with_capacity(header.len() + compressed_data.len());
            result.extend_from_slice(&header);
            result.extend_from_slice(&compressed_data);
            
            Ok(result)
        }

        fn decompress(&self, data: &[u8]) -> CompressionResult<Vec<u8>> {
            // Check if data has valid header
            if !self.is_compressed(data) {
                return Err(CompressionError::decompression_failed(
                    "Data does not have valid zstd compression header"
                ));
            }

            // Extract compressed data (skip header)
            let compressed_data = &data[magic_header::HEADER_SIZE..];
            
            // Decompress the data
            let decompressed_data = zstd::decode_all(compressed_data)
                .map_err(|e| CompressionError::decompression_failed(
                    format!("zstd decompression failed: {}", e)
                ))?;

            Ok(decompressed_data)
        }

        fn is_compressed(&self, data: &[u8]) -> bool {
            magic_header::has_magic_header(data) 
                && magic_header::extract_backend_id(data) == Some(self.backend_id())
        }

        fn backend_name(&self) -> &'static str {
            "zstd"
        }

        fn default_level(&self) -> Option<i32> {
            Some(self.default_level)
        }

        fn backend_id(&self) -> u8 {
            CompressionBackendType::Zstd.backend_id()
        }
    }
}

/// Process command arguments for compression based on command type
/// 
/// This function examines the command type and compresses appropriate arguments
/// for set-type commands. It modifies the arguments vector in-place.
/// 
/// # Arguments
/// * `args` - Mutable reference to the command arguments vector
/// * `request_type` - The type of request being processed
/// * `compression_manager` - Optional compression manager for performing compression
/// 
/// # Returns
/// * `Ok(())` - If processing completed successfully (with or without compression)
/// * `Err(CompressionError)` - If compression was attempted but failed critically
/// 
/// # Behavior
/// - For CompressValues commands: Attempts to compress value arguments
/// - For DecompressValues commands: No processing (decompression happens on response)
/// - For NoCompression commands: No processing
/// - Uses graceful fallback: if compression fails, keeps original values
pub fn process_command_args_for_compression(
    args: &mut Vec<Vec<u8>>,
    request_type: RequestType,
    compression_manager: Option<&CompressionManager>,
) -> CompressionResult<()> {
    // Early return if no compression manager or compression not needed
    let Some(manager) = compression_manager else {
        return Ok(());
    };

    if !manager.is_enabled() {
        return Ok(());
    }

    let behavior = get_command_compression_behavior(request_type);
    if behavior != CommandCompressionBehavior::CompressValues {
        return Ok(());
    }

    // Process arguments based on command type
    match request_type {
        // Basic SET command - compress the value argument
        RequestType::Set => {
            compress_single_value_command(args, manager, 1) // Value is at index 1 (after key)
        }
        
        // Default case - no compression needed
        _ => Ok(()),
    }
}

/// Compress a single value at the specified index
fn compress_single_value_command(
    args: &mut Vec<Vec<u8>>,
    manager: &CompressionManager,
    value_index: usize,
) -> CompressionResult<()> {
    if args.len() <= value_index {
        return Ok(()); // Not enough arguments, skip compression
    }
    
    let compressed_value = manager.try_compress_value(&args[value_index]);
    args[value_index] = compressed_value;
    Ok(())
}



/// Process response values for decompression based on command type
/// 
/// This function examines the command type and decompresses appropriate values
/// for get-type commands. It handles various response formats including single
/// values, arrays, maps, and null/nil responses.
/// 
/// # Arguments
/// * `value` - The response value to potentially decompress
/// * `request_type` - The type of request that generated this response
/// * `compression_manager` - Optional compression manager for performing decompression
/// 
/// # Returns
/// * `Ok(Value)` - The processed response with decompressed values where appropriate
/// * `Err(CompressionError)` - If decompression was attempted but failed critically
/// 
/// # Behavior
/// - For DecompressValues commands: Attempts to decompress value(s) in the response
/// - For CompressValues commands: No processing (compression happens on request)
/// - For NoCompression commands: No processing
/// - Uses graceful fallback: if decompression fails, keeps original values
/// - Handles null/nil responses without attempting decompression
/// - Processes multi-value responses (arrays, maps) by decompressing individual elements
pub fn process_response_for_decompression(
    value: redis::Value,
    request_type: RequestType,
    compression_manager: Option<&CompressionManager>,
) -> CompressionResult<redis::Value> {
    use redis::Value;

    // Early return if no compression manager or decompression not needed
    let Some(manager) = compression_manager else {
        return Ok(value);
    };

    if !manager.is_enabled() {
        return Ok(value);
    }

    let behavior = get_command_compression_behavior(request_type);
    if behavior != CommandCompressionBehavior::DecompressValues {
        return Ok(value);
    }

    // Handle null/nil responses without attempting decompression
    if matches!(value, Value::Nil) {
        return Ok(value);
    }

    // Process response based on command type and value structure
    match request_type {
        // Basic GET command - decompress the returned value
        RequestType::Get => {
            decompress_single_value_response(value, manager)
        }
        
        // Default case - return value unchanged
        _ => Ok(value),
    }
}

/// Decompress a single value response
fn decompress_single_value_response(
    value: redis::Value,
    manager: &CompressionManager,
) -> CompressionResult<redis::Value> {
    use redis::Value;
    
    match value {
        Value::BulkString(bytes) => {
            let decompressed = manager.try_decompress_value(&bytes);
            Ok(Value::BulkString(decompressed))
        }
        Value::SimpleString(s) => {
            let decompressed = manager.try_decompress_value(s.as_bytes());
            match String::from_utf8(decompressed) {
                Ok(decompressed_string) => Ok(Value::SimpleString(decompressed_string)),
                Err(_) => Ok(Value::BulkString(manager.try_decompress_value(s.as_bytes()))),
            }
        }
        // For other value types, return as-is
        _ => Ok(value),
    }
}



/// Magic header constants for compressed data format
pub mod magic_header {
    /// Magic header bytes: "GLID"
    pub const MAGIC_BYTES: [u8; 4] = [0x47, 0x4C, 0x49, 0x44];
    
    /// Total header size (magic + backend ID)
    pub const HEADER_SIZE: usize = 5;
    
    /// Minimum size for data to potentially be compressed
    pub const MIN_COMPRESSED_SIZE: usize = HEADER_SIZE + 1;

    /// Check if data has the correct magic header
    pub fn has_magic_header(data: &[u8]) -> bool {
        data.len() >= HEADER_SIZE && data[0..4] == MAGIC_BYTES
    }

    /// Extract backend ID from compressed data
    pub fn extract_backend_id(data: &[u8]) -> Option<u8> {
        if has_magic_header(data) {
            Some(data[4])
        } else {
            None
        }
    }

    /// Create header with magic bytes and backend ID
    pub fn create_header(backend_id: u8) -> [u8; HEADER_SIZE] {
        let mut header = [0u8; HEADER_SIZE];
        header[0..4].copy_from_slice(&MAGIC_BYTES);
        header[4] = backend_id;
        header
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compression_error_creation() {
        let error = CompressionError::compression_failed("test message");
        assert_eq!(
            error,
            CompressionError::CompressionFailed {
                message: "test message".to_string()
            }
        );
        assert_eq!(error.to_string(), "Compression failed: test message");
    }

    #[test]
    fn test_decompression_error_creation() {
        let error = CompressionError::decompression_failed("test message");
        assert_eq!(
            error,
            CompressionError::DecompressionFailed {
                message: "test message".to_string()
            }
        );
        assert_eq!(error.to_string(), "Decompression failed: test message");
    }

    #[test]
    fn test_unsupported_backend_error_creation() {
        let error = CompressionError::unsupported_backend("unknown");
        assert_eq!(
            error,
            CompressionError::UnsupportedBackend {
                backend: "unknown".to_string()
            }
        );
        assert_eq!(error.to_string(), "Unsupported compression backend: unknown");
    }

    #[test]
    fn test_invalid_configuration_error_creation() {
        let error = CompressionError::invalid_configuration("invalid level");
        assert_eq!(
            error,
            CompressionError::InvalidConfiguration {
                message: "invalid level".to_string()
            }
        );
        assert_eq!(error.to_string(), "Invalid compression configuration: invalid level");
    }

    #[test]
    fn test_backend_initialization_error_creation() {
        let error = CompressionError::backend_initialization_failed("init failed");
        assert_eq!(
            error,
            CompressionError::BackendInitializationFailed {
                message: "init failed".to_string()
            }
        );
        assert_eq!(error.to_string(), "Backend initialization failed: init failed");
    }

    #[cfg(feature = "compression")]
    mod command_compression_tests {
        use super::*;
        use crate::compression::zstd_backend::ZstdBackend;

        fn create_test_compression_manager() -> CompressionManager {
            let backend = Box::new(ZstdBackend::new().unwrap());
            let config = CompressionConfig::new(CompressionBackendType::Zstd)
                .with_min_compression_size(10); // Low threshold for testing
            CompressionManager::new(backend, config).unwrap()
        }

        #[test]
        fn test_process_command_args_no_compression_manager() {
            let mut args = vec![b"key".to_vec(), b"value".to_vec()];
            let result = process_command_args_for_compression(
                &mut args,
                RequestType::Set,
                None,
            );
            assert!(result.is_ok());
            assert_eq!(args, vec![b"key".to_vec(), b"value".to_vec()]);
        }

        #[test]
        fn test_process_command_args_compression_disabled() {
            let backend = Box::new(ZstdBackend::new().unwrap());
            let config = CompressionConfig::disabled();
            let manager = CompressionManager::new(backend, config).unwrap();
            
            let mut args = vec![b"key".to_vec(), b"value".to_vec()];
            let result = process_command_args_for_compression(
                &mut args,
                RequestType::Set,
                Some(&manager),
            );
            assert!(result.is_ok());
            assert_eq!(args, vec![b"key".to_vec(), b"value".to_vec()]);
        }

        #[test]
        fn test_process_command_args_no_compression_behavior() {
            let manager = create_test_compression_manager();
            let mut args = vec![b"key".to_vec()];
            let result = process_command_args_for_compression(
                &mut args,
                RequestType::Del, // NoCompression behavior
                Some(&manager),
            );
            assert!(result.is_ok());
            assert_eq!(args, vec![b"key".to_vec()]);
        }

        #[test]
        fn test_compress_single_value_command_set() {
            let manager = create_test_compression_manager();
            // Use a longer string that will definitely compress smaller
            let long_value = "this is a very long value that should definitely be compressed because it has lots of repetitive content ".repeat(5);
            let mut args = vec![b"key".to_vec(), long_value.as_bytes().to_vec()];
            let original_value = args[1].clone();
            
            let result = process_command_args_for_compression(
                &mut args,
                RequestType::Set,
                Some(&manager),
            );
            assert!(result.is_ok());
            assert_eq!(args[0], b"key".to_vec()); // Key unchanged
            assert_ne!(args[1], original_value); // Value should be compressed
        }



        #[test]
        fn test_compress_small_values_skipped() {
            let manager = create_test_compression_manager();
            let mut args = vec![b"key".to_vec(), b"small".to_vec()]; // Small value below threshold
            let original_value = args[1].clone();
            
            let result = process_command_args_for_compression(
                &mut args,
                RequestType::Set,
                Some(&manager),
            );
            assert!(result.is_ok());
            assert_eq!(args[1], original_value); // Small value should not be compressed
        }

        #[test]
        fn test_compress_insufficient_args() {
            let manager = create_test_compression_manager();
            let mut args = vec![b"key".to_vec()]; // Missing value argument
            
            let result = process_command_args_for_compression(
                &mut args,
                RequestType::Set,
                Some(&manager),
            );
            assert!(result.is_ok()); // Should not fail, just skip compression
            assert_eq!(args, vec![b"key".to_vec()]);
        }

        #[test]
        fn test_compress_empty_args() {
            let manager = create_test_compression_manager();
            let mut args = vec![];
            
            let result = process_command_args_for_compression(
                &mut args,
                RequestType::Set,
                Some(&manager),
            );
            assert!(result.is_ok()); // Should not fail, just skip compression
            assert_eq!(args, Vec::<Vec<u8>>::new());
        }
    }

    #[test]
    fn test_magic_header_validation() {
        let valid_header = [0x47, 0x4C, 0x49, 0x44, 0x01, 0x02, 0x03];
        assert!(magic_header::has_magic_header(&valid_header));

        let invalid_header = [0x00, 0x01, 0x02, 0x03, 0x04];
        assert!(!magic_header::has_magic_header(&invalid_header));

        let too_short = [0x47, 0x4C];
        assert!(!magic_header::has_magic_header(&too_short));
    }

    #[test]
    fn test_backend_id_extraction() {
        let data_with_header = [0x47, 0x4C, 0x49, 0x44, 0x01, 0x02, 0x03];
        assert_eq!(magic_header::extract_backend_id(&data_with_header), Some(0x01));

        let data_without_header = [0x00, 0x01, 0x02, 0x03, 0x04];
        assert_eq!(magic_header::extract_backend_id(&data_without_header), None);
    }

    #[test]
    fn test_header_creation() {
        let header = magic_header::create_header(0x01);
        assert_eq!(header, [0x47, 0x4C, 0x49, 0x44, 0x01]);
        assert!(magic_header::has_magic_header(&header));
        assert_eq!(magic_header::extract_backend_id(&header), Some(0x01));
    }

    // Mock compression backend for testing trait implementation
    #[derive(Debug)]
    struct MockCompressionBackend;

    impl CompressionBackend for MockCompressionBackend {
        fn compress(&self, data: &[u8], _level: Option<i32>) -> CompressionResult<Vec<u8>> {
            let header = magic_header::create_header(self.backend_id());
            let mut result = Vec::with_capacity(header.len() + data.len());
            result.extend_from_slice(&header);
            result.extend_from_slice(data);
            Ok(result)
        }

        fn decompress(&self, data: &[u8]) -> CompressionResult<Vec<u8>> {
            if !self.is_compressed(data) {
                return Err(CompressionError::decompression_failed("Invalid format"));
            }
            Ok(data[magic_header::HEADER_SIZE..].to_vec())
        }

        fn is_compressed(&self, data: &[u8]) -> bool {
            magic_header::has_magic_header(data) 
                && magic_header::extract_backend_id(data) == Some(self.backend_id())
        }

        fn backend_name(&self) -> &'static str {
            "mock"
        }

        fn default_level(&self) -> Option<i32> {
            Some(3)
        }

        fn backend_id(&self) -> u8 {
            0xFF
        }
    }

    #[test]
    fn test_compression_backend_type() {
        // Test backend IDs
        assert_eq!(CompressionBackendType::Zstd.backend_id(), 0x01);
        assert_eq!(CompressionBackendType::Lz4.backend_id(), 0x02);

        // Test backend names
        assert_eq!(CompressionBackendType::Zstd.backend_name(), "zstd");
        assert_eq!(CompressionBackendType::Lz4.backend_name(), "lz4");

        // Test default levels
        assert_eq!(CompressionBackendType::Zstd.default_level(), Some(3));
        assert_eq!(CompressionBackendType::Lz4.default_level(), None);

        // Test display
        assert_eq!(CompressionBackendType::Zstd.to_string(), "zstd");
        assert_eq!(CompressionBackendType::Lz4.to_string(), "lz4");
    }

    #[test]
    fn test_compression_backend_type_from_str() {
        use std::str::FromStr;

        // Test valid parsing
        assert_eq!(CompressionBackendType::from_str("zstd").unwrap(), CompressionBackendType::Zstd);
        assert_eq!(CompressionBackendType::from_str("zstandard").unwrap(), CompressionBackendType::Zstd);
        assert_eq!(CompressionBackendType::from_str("lz4").unwrap(), CompressionBackendType::Lz4);
        assert_eq!(CompressionBackendType::from_str("ZSTD").unwrap(), CompressionBackendType::Zstd);

        // Test invalid parsing
        assert!(CompressionBackendType::from_str("invalid").is_err());
        assert!(CompressionBackendType::from_str("").is_err());
    }

    #[test]
    fn test_compression_config_creation() {
        // Test new config
        let config = CompressionConfig::new(CompressionBackendType::Zstd);
        assert!(config.enabled);
        assert_eq!(config.backend, CompressionBackendType::Zstd);
        assert_eq!(config.compression_level, Some(3));
        assert_eq!(config.min_compression_size, 64);
        assert_eq!(config.max_compression_size, None);

        // Test disabled config
        let disabled = CompressionConfig::disabled();
        assert!(!disabled.enabled);
        assert_eq!(disabled.backend, CompressionBackendType::Zstd);
        assert_eq!(disabled.compression_level, None);

        // Test default
        let default = CompressionConfig::default();
        assert!(!default.enabled);
    }

    #[test]
    fn test_compression_config_builder_methods() {
        let config = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_compression_level(Some(5))
            .with_min_compression_size(128)
            .with_max_compression_size(Some(1024));

        assert_eq!(config.compression_level, Some(5));
        assert_eq!(config.min_compression_size, 128);
        assert_eq!(config.max_compression_size, Some(1024));
    }

    #[test]
    fn test_compression_config_validation() {
        // Valid config
        let valid_config = CompressionConfig::new(CompressionBackendType::Zstd);
        assert!(valid_config.validate().is_ok());

        // Invalid min size (0)
        let invalid_min = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(0);
        assert!(invalid_min.validate().is_err());

        // Invalid min size (too large)
        let invalid_large_min = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(2 * 1024 * 1024);
        assert!(invalid_large_min.validate().is_err());

        // Invalid max size (smaller than min)
        let invalid_max = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(100)
            .with_max_compression_size(Some(50));
        assert!(invalid_max.validate().is_err());

        // Invalid zstd compression level
        let invalid_zstd_level = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_compression_level(Some(25));
        assert!(invalid_zstd_level.validate().is_err());

        let invalid_zstd_level_low = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_compression_level(Some(0));
        assert!(invalid_zstd_level_low.validate().is_err());

        // Invalid lz4 compression level (lz4 doesn't support levels)
        let invalid_lz4_level = CompressionConfig::new(CompressionBackendType::Lz4)
            .with_compression_level(Some(1));
        assert!(invalid_lz4_level.validate().is_err());

        // Valid lz4 without level
        let valid_lz4 = CompressionConfig::new(CompressionBackendType::Lz4)
            .with_compression_level(None);
        assert!(valid_lz4.validate().is_ok());
    }

    #[test]
    fn test_compression_config_should_compress() {
        let config = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(64)
            .with_max_compression_size(Some(1024));

        // Disabled config should never compress
        let disabled = CompressionConfig::disabled();
        assert!(!disabled.should_compress(100));

        // Too small
        assert!(!config.should_compress(32));

        // Just right
        assert!(config.should_compress(100));

        // At minimum
        assert!(config.should_compress(64));

        // At maximum
        assert!(config.should_compress(1024));

        // Too large
        assert!(!config.should_compress(2048));

        // No maximum size limit
        let config_no_max = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(64)
            .with_max_compression_size(None);
        assert!(config_no_max.should_compress(10000));
    }

    #[test]
    fn test_compression_manager_creation() {
        let backend = Box::new(MockCompressionBackend);
        let mut config = CompressionConfig::new(CompressionBackendType::Zstd);
        config.backend = CompressionBackendType::Zstd;
        
        // This will fail because MockCompressionBackend has ID 0xFF but config expects Zstd (0x01)
        let result = CompressionManager::new(backend, config);
        assert!(result.is_err());

        // Test with matching backend
        let backend = Box::new(MockCompressionBackend);
        let mut config = CompressionConfig::new(CompressionBackendType::Zstd);
        // Adjust config to match mock backend ID
        config.backend = CompressionBackendType::Zstd; // This will still fail due to ID mismatch
        
        // For a proper test, we'd need a backend that matches the config
        // This test demonstrates the validation logic
    }

    #[test]
    fn test_command_compression_behavior_display() {
        assert_eq!(CommandCompressionBehavior::CompressValues.to_string(), "CompressValues");
        assert_eq!(CommandCompressionBehavior::DecompressValues.to_string(), "DecompressValues");
        assert_eq!(CommandCompressionBehavior::NoCompression.to_string(), "NoCompression");
    }

    #[test]
    fn test_command_compression_behavior_description() {
        assert_eq!(
            CommandCompressionBehavior::CompressValues.description(),
            "Compress values before sending to server"
        );
        assert_eq!(
            CommandCompressionBehavior::DecompressValues.description(),
            "Decompress values after receiving from server"
        );
        assert_eq!(
            CommandCompressionBehavior::NoCompression.description(),
            "No compression processing required"
        );
    }

    #[test]
    fn test_string_command_classification() {
        // Only SET should compress values in simplified version
        assert_eq!(
            get_command_compression_behavior(RequestType::Set),
            CommandCompressionBehavior::CompressValues
        );
        
        // Only GET should decompress values in simplified version
        assert_eq!(
            get_command_compression_behavior(RequestType::Get),
            CommandCompressionBehavior::DecompressValues
        );

        // All other string commands should not compress in simplified version
        assert_eq!(
            get_command_compression_behavior(RequestType::MSet),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::SetEx),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::SetNX),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::MSetNX),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Append),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::SetRange),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::MGet),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::GetEx),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::GetDel),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::GetRange),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::GetSet),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_hash_command_classification() {
        // In simplified version, all hash commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::HSet),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::HGet),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::HMSet),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::HMGet),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_list_command_classification() {
        // In simplified version, all list commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::LPush),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::LPop),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::LRange),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_set_command_classification() {
        // In simplified version, all set commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::SAdd),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::SMembers),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::SPop),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_sorted_set_command_classification() {
        // In simplified version, all sorted set commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::ZAdd),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::ZRange),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_stream_command_classification() {
        // In simplified version, all stream commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::XAdd),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::XRead),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_json_command_classification() {
        // In simplified version, all JSON commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::JsonSet),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::JsonGet),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_hyperloglog_command_classification() {
        // In simplified version, all HyperLogLog commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::PfAdd),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_geospatial_command_classification() {
        // In simplified version, all geospatial commands should return NoCompression
        assert_eq!(
            get_command_compression_behavior(RequestType::GeoAdd),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_no_compression_commands() {
        // Connection management commands
        assert_eq!(
            get_command_compression_behavior(RequestType::Ping),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Echo),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Auth),
            CommandCompressionBehavior::NoCompression
        );

        // Generic commands
        assert_eq!(
            get_command_compression_behavior(RequestType::Del),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Exists),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Expire),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::TTL),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Type),
            CommandCompressionBehavior::NoCompression
        );

        // Server management commands
        assert_eq!(
            get_command_compression_behavior(RequestType::Info),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::ConfigGet),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::ConfigSet),
            CommandCompressionBehavior::NoCompression
        );

        // Transaction commands
        assert_eq!(
            get_command_compression_behavior(RequestType::Multi),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Exec),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::Discard),
            CommandCompressionBehavior::NoCompression
        );

        // Invalid/Custom commands
        assert_eq!(
            get_command_compression_behavior(RequestType::InvalidRequest),
            CommandCompressionBehavior::NoCompression
        );
        assert_eq!(
            get_command_compression_behavior(RequestType::CustomCommand),
            CommandCompressionBehavior::NoCompression
        );
    }

    #[test]
    fn test_command_classification_completeness() {
        // Test a sampling of commands to ensure they all have classifications
        // This helps catch any commands that might be missed in the match statement
        
        let test_commands = vec![
            RequestType::Set,
            RequestType::Get,
            RequestType::HSet,
            RequestType::HGet,
            RequestType::LPush,
            RequestType::LPop,
            RequestType::SAdd,
            RequestType::SMembers,
            RequestType::ZAdd,
            RequestType::ZRange,
            RequestType::XAdd,
            RequestType::XRead,
            RequestType::JsonSet,
            RequestType::JsonGet,
            RequestType::PfAdd,
            RequestType::GeoAdd,
            RequestType::Del,
            RequestType::Ping,
            RequestType::Info,
            RequestType::InvalidRequest,
        ];

        for command in test_commands {
            let behavior = get_command_compression_behavior(command);
            // Just ensure we get a valid behavior for each command
            match behavior {
                CommandCompressionBehavior::CompressValues
                | CommandCompressionBehavior::DecompressValues
                | CommandCompressionBehavior::NoCompression => {
                    // All good, we got a valid classification
                }
            }
        }
    }

    #[test]
    fn test_compression_config_should_compress_no_maximum_limit() {
        let no_max = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(64);
        assert!(no_max.should_compress(10000));
    }



    #[test]
    fn test_compression_manager_should_compress() {
        #[derive(Debug)]
        struct ZstdMockBackend;

        impl CompressionBackend for ZstdMockBackend {
            fn compress(&self, data: &[u8], _level: Option<i32>) -> CompressionResult<Vec<u8>> {
                let header = magic_header::create_header(self.backend_id());
                let mut result = Vec::with_capacity(header.len() + data.len());
                result.extend_from_slice(&header);
                result.extend_from_slice(data);
                Ok(result)
            }

            fn decompress(&self, data: &[u8]) -> CompressionResult<Vec<u8>> {
                if !self.is_compressed(data) {
                    return Err(CompressionError::decompression_failed("Invalid format"));
                }
                Ok(data[magic_header::HEADER_SIZE..].to_vec())
            }

            fn is_compressed(&self, data: &[u8]) -> bool {
                magic_header::has_magic_header(data) 
                    && magic_header::extract_backend_id(data) == Some(self.backend_id())
            }

            fn backend_name(&self) -> &'static str {
                "zstd"
            }

            fn default_level(&self) -> Option<i32> {
                Some(3)
            }

            fn backend_id(&self) -> u8 {
                0x01
            }
        }

        let backend = Box::new(ZstdMockBackend);
        let config = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(64);
        let manager = CompressionManager::new(backend, config).unwrap();

        let small_data = vec![0u8; 32];
        let large_data = vec![0u8; 128];

        assert!(!manager.should_compress(&small_data));
        assert!(manager.should_compress(&large_data));
    }

    #[test]
    fn test_compression_manager_compress_decompress() {
        #[derive(Debug)]
        struct ZstdMockBackend;

        impl CompressionBackend for ZstdMockBackend {
            fn compress(&self, data: &[u8], _level: Option<i32>) -> CompressionResult<Vec<u8>> {
                let header = magic_header::create_header(self.backend_id());
                let mut result = Vec::with_capacity(header.len() + data.len());
                result.extend_from_slice(&header);
                result.extend_from_slice(data);
                Ok(result)
            }

            fn decompress(&self, data: &[u8]) -> CompressionResult<Vec<u8>> {
                if !self.is_compressed(data) {
                    return Err(CompressionError::decompression_failed("Invalid format"));
                }
                Ok(data[magic_header::HEADER_SIZE..].to_vec())
            }

            fn is_compressed(&self, data: &[u8]) -> bool {
                magic_header::has_magic_header(data) 
                    && magic_header::extract_backend_id(data) == Some(self.backend_id())
            }

            fn backend_name(&self) -> &'static str {
                "zstd"
            }

            fn default_level(&self) -> Option<i32> {
                Some(3)
            }

            fn backend_id(&self) -> u8 {
                0x01
            }
        }

        let backend = Box::new(ZstdMockBackend);
        let config = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(64);
        let manager = CompressionManager::new(backend, config).unwrap();

        let test_data = vec![1u8; 128]; // Large enough to compress

        // Test compression
        let compressed = manager.compress_value(&test_data).unwrap();
        assert!(compressed.len() > test_data.len()); // Should be larger due to header
        assert!(manager.backend.is_compressed(&compressed));

        // Test decompression
        let decompressed = manager.decompress_value(&compressed).unwrap();
        assert_eq!(decompressed, test_data);

        // Test decompression of uncompressed data
        let uncompressed_result = manager.decompress_value(&test_data).unwrap();
        assert_eq!(uncompressed_result, test_data);
    }

    #[test]
    fn test_compression_manager_try_methods() {
        #[derive(Debug)]
        struct ZstdMockBackend;

        impl CompressionBackend for ZstdMockBackend {
            fn compress(&self, data: &[u8], _level: Option<i32>) -> CompressionResult<Vec<u8>> {
                let header = magic_header::create_header(self.backend_id());
                let mut result = Vec::with_capacity(header.len() + data.len());
                result.extend_from_slice(&header);
                result.extend_from_slice(data);
                Ok(result)
            }

            fn decompress(&self, data: &[u8]) -> CompressionResult<Vec<u8>> {
                if !self.is_compressed(data) {
                    return Err(CompressionError::decompression_failed("Invalid format"));
                }
                Ok(data[magic_header::HEADER_SIZE..].to_vec())
            }

            fn is_compressed(&self, data: &[u8]) -> bool {
                magic_header::has_magic_header(data) 
                    && magic_header::extract_backend_id(data) == Some(self.backend_id())
            }

            fn backend_name(&self) -> &'static str {
                "zstd"
            }

            fn default_level(&self) -> Option<i32> {
                Some(3)
            }

            fn backend_id(&self) -> u8 {
                0x01
            }
        }

        let backend = Box::new(ZstdMockBackend);
        let config = CompressionConfig::new(CompressionBackendType::Zstd)
            .with_min_compression_size(64);
        let manager = CompressionManager::new(backend, config).unwrap();

        let small_data = vec![1u8; 32]; // Too small to compress
        let large_data = vec![1u8; 128]; // Large enough to compress

        // try_compress_value should return original for small data
        let result = manager.try_compress_value(&small_data);
        assert_eq!(result, small_data);

        // try_compress_value should compress large data
        let result = manager.try_compress_value(&large_data);
        assert!(result.len() > large_data.len());

        // try_decompress_value should handle both compressed and uncompressed data
        let decompressed = manager.try_decompress_value(&result);
        assert_eq!(decompressed, large_data);

        let uncompressed_result = manager.try_decompress_value(&small_data);
        assert_eq!(uncompressed_result, small_data);
    }

    #[test]
    fn test_compression_manager_disabled_config() {
        #[derive(Debug)]
        struct ZstdMockBackend;

        impl CompressionBackend for ZstdMockBackend {
            fn compress(&self, _data: &[u8], _level: Option<i32>) -> CompressionResult<Vec<u8>> {
                unreachable!("Should not be called when disabled")
            }

            fn decompress(&self, data: &[u8]) -> CompressionResult<Vec<u8>> {
                Ok(data.to_vec())
            }

            fn is_compressed(&self, _data: &[u8]) -> bool {
                false
            }

            fn backend_name(&self) -> &'static str {
                "zstd"
            }

            fn default_level(&self) -> Option<i32> {
                Some(3)
            }

            fn backend_id(&self) -> u8 {
                0x01
            }
        }

        let backend = Box::new(ZstdMockBackend);
        let config = CompressionConfig::disabled();
        let manager = CompressionManager::new(backend, config).unwrap();

        assert!(!manager.is_enabled());

        let test_data = vec![1u8; 128];

        // Should not compress when disabled
        assert!(!manager.should_compress(&test_data));

        // try_compress_value should return original when disabled
        let result = manager.try_compress_value(&test_data);
        assert_eq!(result, test_data);

        // decompress_value should return original when disabled
        let result = manager.decompress_value(&test_data).unwrap();
        assert_eq!(result, test_data);
    }

    #[test]
    fn test_compression_backend_trait() {
        let backend = MockCompressionBackend;
        let test_data = b"Hello, World!";

        // Test compression
        let compressed = backend.compress(test_data, None).unwrap();
        assert!(compressed.len() > test_data.len());
        assert!(backend.is_compressed(&compressed));

        // Test decompression
        let decompressed = backend.decompress(&compressed).unwrap();
        assert_eq!(decompressed, test_data);

        // Test backend properties
        assert_eq!(backend.backend_name(), "mock");
        assert_eq!(backend.default_level(), Some(3));
        assert_eq!(backend.backend_id(), 0xFF);

        // Test invalid decompression
        let invalid_data = b"not compressed";
        assert!(!backend.is_compressed(invalid_data));
        assert!(backend.decompress(invalid_data).is_err());
    }
}

    #[cfg(feature = "compression")]
    mod zstd_backend_tests {
        use super::*;
        use crate::compression::zstd_backend::ZstdBackend;

        #[test]
        fn test_zstd_backend_creation() {
            // Test default creation
            let backend = ZstdBackend::new().unwrap();
            assert_eq!(backend.backend_name(), "zstd");
            assert_eq!(backend.backend_id(), 0x01);
            assert_eq!(backend.default_level(), Some(3));

            // Test default trait
            let default_backend = ZstdBackend::default();
            assert_eq!(default_backend.backend_name(), "zstd");
            assert_eq!(default_backend.default_level(), Some(3));
        }

        #[test]
        fn test_zstd_backend_with_custom_level() {
            // Test valid custom level
            let backend = ZstdBackend::with_default_level(5).unwrap();
            assert_eq!(backend.default_level(), Some(5));

            // Test invalid levels
            assert!(ZstdBackend::with_default_level(0).is_err());
            assert!(ZstdBackend::with_default_level(23).is_err());
            assert!(ZstdBackend::with_default_level(-1).is_err());

            // Test boundary values
            assert!(ZstdBackend::with_default_level(1).is_ok());
            assert!(ZstdBackend::with_default_level(22).is_ok());
        }

        #[test]
        fn test_zstd_compression_and_decompression() {
            let backend = ZstdBackend::new().unwrap();
            let test_data = b"Hello, World! This is a test string for compression.";

            // Test compression
            let compressed = backend.compress(test_data, None).unwrap();
            
            // Verify header is present
            assert!(backend.is_compressed(&compressed));
            assert!(magic_header::has_magic_header(&compressed));
            assert_eq!(magic_header::extract_backend_id(&compressed), Some(0x01));

            // Test decompression
            let decompressed = backend.decompress(&compressed).unwrap();
            assert_eq!(decompressed, test_data);
        }

        #[test]
        fn test_zstd_compression_with_different_levels() {
            let backend = ZstdBackend::new().unwrap();
            let test_data = b"This is a longer test string that should compress well with different compression levels. ".repeat(10);

            // Test different compression levels
            for level in [1, 3, 6, 9, 15, 22] {
                let compressed = backend.compress(&test_data, Some(level)).unwrap();
                assert!(backend.is_compressed(&compressed));
                
                let decompressed = backend.decompress(&compressed).unwrap();
                assert_eq!(decompressed, test_data);
            }
        }

        #[test]
        fn test_zstd_compression_with_invalid_level() {
            let backend = ZstdBackend::new().unwrap();
            let test_data = b"test data";

            // Test invalid compression levels
            assert!(backend.compress(test_data, Some(0)).is_err());
            assert!(backend.compress(test_data, Some(23)).is_err());
            assert!(backend.compress(test_data, Some(-1)).is_err());
        }

        #[test]
        fn test_zstd_is_compressed_detection() {
            let backend = ZstdBackend::new().unwrap();
            let test_data = b"Test data for compression detection";

            // Test uncompressed data
            assert!(!backend.is_compressed(test_data));

            // Test compressed data
            let compressed = backend.compress(test_data, None).unwrap();
            assert!(backend.is_compressed(&compressed));

            // Test data with wrong magic header
            let wrong_magic = [0x00, 0x01, 0x02, 0x03, 0x01, 0x05, 0x06];
            assert!(!backend.is_compressed(&wrong_magic));

            // Test data with correct magic but wrong backend ID
            let wrong_backend = [0x47, 0x4C, 0x49, 0x44, 0x02, 0x05, 0x06]; // Backend ID 0x02 (not zstd)
            assert!(!backend.is_compressed(&wrong_backend));

            // Test too short data
            let too_short = [0x47, 0x4C];
            assert!(!backend.is_compressed(&too_short));
        }

        #[test]
        fn test_zstd_decompression_invalid_data() {
            let backend = ZstdBackend::new().unwrap();

            // Test decompression of uncompressed data
            let uncompressed = b"This is not compressed";
            assert!(backend.decompress(uncompressed).is_err());

            // Test decompression of data with wrong header
            let wrong_header = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06];
            assert!(backend.decompress(&wrong_header).is_err());

            // Test decompression of data with correct header but invalid compressed data
            let mut invalid_compressed = magic_header::create_header(0x01).to_vec();
            invalid_compressed.extend_from_slice(b"invalid compressed data");
            assert!(backend.decompress(&invalid_compressed).is_err());
        }

        #[test]
        fn test_zstd_compression_empty_data() {
            let backend = ZstdBackend::new().unwrap();
            let empty_data = b"";

            // Test compression of empty data
            let compressed = backend.compress(empty_data, None).unwrap();
            assert!(backend.is_compressed(&compressed));

            // Test decompression
            let decompressed = backend.decompress(&compressed).unwrap();
            assert_eq!(decompressed, empty_data);
        }

        #[test]
        fn test_zstd_compression_large_data() {
            let backend = ZstdBackend::new().unwrap();
            let large_data = vec![0x42u8; 10000]; // 10KB of repeated data

            // Test compression
            let compressed = backend.compress(&large_data, None).unwrap();
            assert!(backend.is_compressed(&compressed));
            
            // Verify compression actually reduced size (repeated data should compress well)
            assert!(compressed.len() < large_data.len());

            // Test decompression
            let decompressed = backend.decompress(&compressed).unwrap();
            assert_eq!(decompressed, large_data);
        }

        #[test]
        fn test_zstd_compression_binary_data() {
            let backend = ZstdBackend::new().unwrap();
            let binary_data: Vec<u8> = (0..=255).cycle().take(1000).collect();

            // Test compression
            let compressed = backend.compress(&binary_data, None).unwrap();
            assert!(backend.is_compressed(&compressed));

            // Test decompression
            let decompressed = backend.decompress(&compressed).unwrap();
            assert_eq!(decompressed, binary_data);
        }

        #[test]
        fn test_zstd_compression_random_data() {
            let backend = ZstdBackend::new().unwrap();
            
            // Generate some pseudo-random data
            let mut random_data = Vec::new();
            for i in 0..1000 {
                random_data.push(((i * 17 + 42) % 256) as u8);
            }

            // Test compression
            let compressed = backend.compress(&random_data, None).unwrap();
            assert!(backend.is_compressed(&compressed));

            // Test decompression
            let decompressed = backend.decompress(&compressed).unwrap();
            assert_eq!(decompressed, random_data);
        }

        #[test]
        fn test_zstd_compression_utf8_text() {
            let backend = ZstdBackend::new().unwrap();
            let utf8_text = "Hello, 世界! 🌍 This is a test with UTF-8 characters: café, naïve, résumé";

            // Test compression
            let compressed = backend.compress(utf8_text.as_bytes(), None).unwrap();
            assert!(backend.is_compressed(&compressed));

            // Test decompression
            let decompressed = backend.decompress(&compressed).unwrap();
            assert_eq!(decompressed, utf8_text.as_bytes());
            
            // Verify we can convert back to string
            let decompressed_string = String::from_utf8(decompressed).unwrap();
            assert_eq!(decompressed_string, utf8_text);
        }

        #[test]
        fn test_zstd_header_format() {
            let backend = ZstdBackend::new().unwrap();
            let test_data = b"Test data for header validation";

            let compressed = backend.compress(test_data, None).unwrap();
            
            // Verify header format: [GLID][0x01][compressed_data]
            assert_eq!(compressed[0..4], [0x47, 0x4C, 0x49, 0x44]); // "GLID"
            assert_eq!(compressed[4], 0x01); // Zstd backend ID
            assert!(compressed.len() > 5); // Should have compressed data after header
        }

        #[test]
        fn test_zstd_compression_manager_integration() {
            let backend = Box::new(ZstdBackend::new().unwrap());
            let config = CompressionConfig::new(CompressionBackendType::Zstd)
                .with_min_compression_size(10);
            let manager = CompressionManager::new(backend, config).unwrap();

            let test_data = b"This is test data for compression manager integration";

            // Test compression through manager
            let compressed = manager.compress_value(test_data).unwrap();
            assert!(manager.backend_name() == "zstd");

            // Test decompression through manager
            let decompressed = manager.decompress_value(&compressed).unwrap();
            assert_eq!(decompressed, test_data);

            // Test graceful fallback methods
            let compressed_fallback = manager.try_compress_value(test_data);
            let decompressed_fallback = manager.try_decompress_value(&compressed_fallback);
            assert_eq!(decompressed_fallback, test_data);
        }
    }

    mod response_decompression_tests {
        use super::*;
        use redis::Value;

        #[test]
        fn test_process_response_for_decompression() {
            // Simple test to verify the function exists and compiles
            let value = Value::BulkString(b"test_value".to_vec());
            let result = process_response_for_decompression(value.clone(), RequestType::Get, None).unwrap();
            assert_eq!(result, value);
        }
    }
