// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Base configuration settings for creating a GLIDE client.
/// Shared settings for standalone and cluster clients.
/// </summary>
public abstract class BaseClientConfiguration
{
    /// <summary>
    /// DNS Addresses and ports of known nodes in the cluster.
    /// </summary>
    public IReadOnlyList<NodeAddress> Addresses { get; }

    /// <summary>
    /// True if communication with the cluster should use Transport Level Security.
    /// </summary>
    public bool UseTls { get; }

    /// <summary>
    /// Represents the client's read from strategy.
    /// </summary>
    public ReadFrom ReadFrom { get; }

    /// <summary>
    /// Credentials for authentication process.
    /// </summary>
    public ServerCredentials? Credentials { get; }

    /// <summary>
    /// The duration in milliseconds that the client should wait for a request to complete.
    /// </summary>
    public uint? RequestTimeout { get; }

    /// <summary>
    /// Client name to be used for the client.
    /// </summary>
    public string? ClientName { get; }

    /// <summary>
    /// Serialization protocol to be used with the server.
    /// </summary>
    public ProtocolVersion Protocol { get; }

    /// <summary>
    /// The maximum number of concurrent requests allowed to be in-flight.
    /// </summary>
    public uint? InflightRequestsLimit { get; }

    /// <summary>
    /// Availability Zone of the client for AZ affinity routing.
    /// </summary>
    public string? ClientAz { get; }

    /// <summary>
    /// Strategy used to determine how and when to reconnect.
    /// </summary>
    public BackoffStrategy? ReconnectStrategy { get; }

    /// <summary>
    /// Index of the logical database to connect to.
    /// </summary>
    public uint? DatabaseId { get; }

    /// <summary>
    /// Enables lazy connection mode, where physical connections are deferred until the first command.
    /// </summary>
    public bool LazyConnect { get; }

    /// <summary>
    /// Compression configuration for automatic compression of values.
    /// When set, values meeting the minimum size threshold will be automatically compressed.
    /// </summary>
    public CompressionConfiguration? Compression { get; init; }

    protected BaseClientConfiguration(
        IReadOnlyList<NodeAddress> addresses,
        bool useTls = false,
        ReadFrom readFrom = ReadFrom.Primary,
        ServerCredentials? credentials = null,
        uint? requestTimeout = null,
        string? clientName = null,
        ProtocolVersion protocol = ProtocolVersion.Resp3,
        uint? inflightRequestsLimit = null,
        string? clientAz = null,
        BackoffStrategy? reconnectStrategy = null,
        uint? databaseId = null,
        bool lazyConnect = false,
        CompressionConfiguration? compression = null)
    {
        Addresses = addresses;
        UseTls = useTls;
        ReadFrom = readFrom;
        Credentials = credentials;
        RequestTimeout = requestTimeout;
        ClientName = clientName;
        Protocol = protocol;
        InflightRequestsLimit = inflightRequestsLimit;
        ClientAz = clientAz;
        ReconnectStrategy = reconnectStrategy;
        DatabaseId = databaseId;
        LazyConnect = lazyConnect;
        Compression = compression;
    }
}
