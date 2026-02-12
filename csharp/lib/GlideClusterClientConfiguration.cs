// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Configuration settings for creating a cluster GLIDE client.
/// </summary>
public class GlideClusterClientConfiguration : BaseClientConfiguration
{
    public GlideClusterClientConfiguration(
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
        : base(addresses, useTls, readFrom, credentials, requestTimeout,
               clientName, protocol, inflightRequestsLimit, clientAz,
               reconnectStrategy, databaseId, lazyConnect, compression)
    {
    }
}
