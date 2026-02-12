// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Represents the address and port of a node in the cluster.
/// </summary>
public class NodeAddress
{
    /// <summary>
    /// The server host. Defaults to "localhost".
    /// </summary>
    public string Host { get; }

    /// <summary>
    /// The server port. Defaults to 6379.
    /// </summary>
    public int Port { get; }

    public NodeAddress(string host = "localhost", int port = 6379)
    {
        Host = host;
        Port = port;
    }
}
