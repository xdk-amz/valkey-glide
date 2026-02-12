// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Represents the compression backend to use for automatic compression.
/// </summary>
public enum CompressionBackend
{
    /// <summary>
    /// Use zstd compression backend. Default compression level is 3.
    /// </summary>
    Zstd = 0,

    /// <summary>
    /// Use lz4 compression backend. Default compression level is 0.
    /// </summary>
    Lz4 = 1,
}
