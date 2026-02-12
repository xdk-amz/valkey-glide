// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

using Google.Protobuf;

namespace Glide;

/// <summary>
/// Serializes client configuration to protobuf ConnectionRequest bytes
/// for passing to the Rust core via FFI.
/// </summary>
public static class ConnectionRequestSerializer
{
    /// <summary>
    /// Serializes a <see cref="BaseClientConfiguration"/> to protobuf bytes.
    /// </summary>
    /// <param name="config">The client configuration to serialize.</param>
    /// <param name="clusterMode">Whether the client is in cluster mode.</param>
    /// <returns>Protobuf-encoded bytes for the ConnectionRequest.</returns>
    public static byte[] Serialize(BaseClientConfiguration config, bool clusterMode)
    {
        var request = new Protobuf.ConnectionRequest
        {
            ClusterModeEnabled = clusterMode,
            TlsMode = config.UseTls
                ? Protobuf.TlsMode.SecureTls
                : Protobuf.TlsMode.NoTls,
            ReadFrom = MapReadFrom(config.ReadFrom),
            Protocol = (Protobuf.ProtocolVersion)(int)config.Protocol,
            LazyConnect = config.LazyConnect,
        };

        // Add addresses
        foreach (var addr in config.Addresses)
        {
            request.Addresses.Add(new Protobuf.NodeAddress
            {
                Host = addr.Host,
                Port = (uint)addr.Port,
            });
        }

        // Set optional fields
        if (config.RequestTimeout.HasValue)
            request.RequestTimeout = config.RequestTimeout.Value;

        if (config.ClientName != null)
            request.ClientName = config.ClientName;

        if (config.InflightRequestsLimit.HasValue)
            request.InflightRequestsLimit = config.InflightRequestsLimit.Value;

        if (config.ClientAz != null)
            request.ClientAz = config.ClientAz;

        if (config.DatabaseId.HasValue)
            request.DatabaseId = config.DatabaseId.Value;

        // Set credentials
        if (config.Credentials != null)
        {
            request.AuthenticationInfo = new Protobuf.AuthenticationInfo
            {
                Password = config.Credentials.Password,
            };
            if (config.Credentials.Username != null)
                request.AuthenticationInfo.Username = config.Credentials.Username;
        }

        // Set reconnect strategy
        if (config.ReconnectStrategy != null)
        {
            request.ConnectionRetryStrategy = new Protobuf.ConnectionRetryStrategy
            {
                NumberOfRetries = (uint)config.ReconnectStrategy.NumOfRetries,
                Factor = (uint)config.ReconnectStrategy.Factor,
                ExponentBase = (uint)config.ReconnectStrategy.ExponentBase,
            };
            if (config.ReconnectStrategy.JitterPercent.HasValue)
                request.ConnectionRetryStrategy.JitterPercent =
                    (uint)config.ReconnectStrategy.JitterPercent.Value;
        }

        // Set compression configuration
        if (config.Compression != null)
        {
            request.CompressionConfig = SerializeCompressionConfig(config.Compression);
        }

        return request.ToByteArray();
    }

    /// <summary>
    /// Converts a <see cref="CompressionConfiguration"/> to its protobuf representation.
    /// </summary>
    internal static Protobuf.CompressionConfig SerializeCompressionConfig(
        CompressionConfiguration compression)
    {
        var protoConfig = new Protobuf.CompressionConfig
        {
            Enabled = compression.Enabled,
            Backend = (Protobuf.CompressionBackend)(int)compression.Backend,
            MinCompressionSize = compression.MinCompressionSize,
        };

        if (compression.CompressionLevel.HasValue)
        {
            protoConfig.CompressionLevel = compression.CompressionLevel.Value;
        }

        return protoConfig;
    }

    private static Protobuf.ReadFrom MapReadFrom(ReadFrom readFrom) => readFrom switch
    {
        ReadFrom.Primary => Protobuf.ReadFrom.Primary,
        ReadFrom.PreferReplica => Protobuf.ReadFrom.PreferReplica,
        ReadFrom.AzAffinity => Protobuf.ReadFrom.Azaffinity,
        ReadFrom.AzAffinityReplicasAndPrimary => Protobuf.ReadFrom.AzaffinityReplicasAndPrimary,
        _ => Protobuf.ReadFrom.Primary,
    };
}
