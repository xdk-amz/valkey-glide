// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Exception thrown when client configuration is invalid.
/// Inherits from <see cref="ArgumentException"/> to follow .NET conventions
/// for parameter/configuration validation errors.
/// </summary>
public class ConfigurationError : ArgumentException
{
    public ConfigurationError(string message) : base(message) { }
    public ConfigurationError(string message, Exception innerException) : base(message, innerException) { }
}
