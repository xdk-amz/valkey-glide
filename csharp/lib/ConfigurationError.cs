// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Exception thrown when client configuration is invalid.
/// </summary>
public class ConfigurationError : Exception
{
    public ConfigurationError(string message) : base(message) { }
    public ConfigurationError(string message, Exception innerException) : base(message, innerException) { }
}
