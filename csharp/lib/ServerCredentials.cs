// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Credentials for authentication with the server.
/// </summary>
public class ServerCredentials
{
    public string? Username { get; }
    public string Password { get; }

    public ServerCredentials(string password, string? username = null)
    {
        Password = password;
        Username = username;
    }
}
