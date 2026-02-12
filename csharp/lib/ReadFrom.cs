// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Represents the client's read from strategy.
/// </summary>
public enum ReadFrom
{
    /// <summary>
    /// Always get from primary, in order to get the freshest data.
    /// </summary>
    Primary = 0,

    /// <summary>
    /// Spread the requests between all replicas in a round robin manner.
    /// If no replica is available, route the requests to the primary.
    /// </summary>
    PreferReplica = 1,

    /// <summary>
    /// Spread the read requests between replicas in the same client's AZ in a round robin manner,
    /// falling back to other replicas or the primary if needed.
    /// </summary>
    AzAffinity = 3,

    /// <summary>
    /// Spread the read requests among nodes within the client's AZ in a round robin manner,
    /// prioritizing local replicas, then the local primary, and falling back to any replica or the primary if needed.
    /// </summary>
    AzAffinityReplicasAndPrimary = 4,
}
