// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Provides compression and connection statistics for the client.
/// Maps to the FFI Statistics struct exposed by glide-core.
/// </summary>
public class Statistics
{
    /// <summary>Total number of connections opened to Valkey.</summary>
    public ulong TotalConnections { get; init; }

    /// <summary>Total number of GLIDE clients.</summary>
    public ulong TotalClients { get; init; }

    /// <summary>Total number of values compressed.</summary>
    public ulong TotalValuesCompressed { get; init; }

    /// <summary>Total number of values decompressed.</summary>
    public ulong TotalValuesDecompressed { get; init; }

    /// <summary>Total original bytes before compression.</summary>
    public ulong TotalOriginalBytes { get; init; }

    /// <summary>Total bytes after compression.</summary>
    public ulong TotalBytesCompressed { get; init; }

    /// <summary>Total bytes after decompression.</summary>
    public ulong TotalBytesDecompressed { get; init; }

    /// <summary>Number of times compression was skipped.</summary>
    public ulong CompressionSkippedCount { get; init; }

    /// <summary>Number of times subscriptions were out of sync during reconciliation.</summary>
    public ulong SubscriptionOutOfSyncCount { get; init; }

    /// <summary>Timestamp of last successful subscription sync (milliseconds since epoch).</summary>
    public ulong SubscriptionLastSyncTimestamp { get; init; }

    /// <summary>
    /// Returns a dictionary representation of the statistics, matching the Python binding's format.
    /// </summary>
    public Dictionary<string, ulong> ToDictionary() => new()
    {
        ["total_connections"] = TotalConnections,
        ["total_clients"] = TotalClients,
        ["total_values_compressed"] = TotalValuesCompressed,
        ["total_values_decompressed"] = TotalValuesDecompressed,
        ["total_original_bytes"] = TotalOriginalBytes,
        ["total_bytes_compressed"] = TotalBytesCompressed,
        ["total_bytes_decompressed"] = TotalBytesDecompressed,
        ["compression_skipped_count"] = CompressionSkippedCount,
        ["subscription_out_of_sync_count"] = SubscriptionOutOfSyncCount,
        ["subscription_last_sync_timestamp"] = SubscriptionLastSyncTimestamp,
    };

    public override string ToString() =>
        $"Statistics {{ TotalValuesCompressed={TotalValuesCompressed}, " +
        $"TotalValuesDecompressed={TotalValuesDecompressed}, " +
        $"TotalOriginalBytes={TotalOriginalBytes}, " +
        $"TotalBytesCompressed={TotalBytesCompressed}, " +
        $"TotalBytesDecompressed={TotalBytesDecompressed}, " +
        $"CompressionSkippedCount={CompressionSkippedCount} }}";
}
