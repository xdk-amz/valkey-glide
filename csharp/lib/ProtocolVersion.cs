// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Represents the communication protocol with the server.
/// </summary>
public enum ProtocolVersion
{
    /// <summary>
    /// Communicate using RESP3.
    /// </summary>
    Resp3 = 0,

    /// <summary>
    /// Communicate using RESP2.
    /// </summary>
    Resp2 = 1,
}
