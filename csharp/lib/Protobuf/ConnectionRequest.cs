// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0
// Generated from glide-core/src/protobuf/connection_request.proto
// This file provides C# protobuf message classes matching the connection_request.proto schema.
//
// TODO(tech-debt): Replace this hand-written protobuf code with auto-generated code from protoc.
// The Java and Python bindings use generated protobuf classes. Hand-written protobuf is fragile —
// any proto schema change requires manual updates here. To generate, run:
//   protoc --csharp_out=csharp/lib/Protobuf glide-core/src/protobuf/connection_request.proto

using Google.Protobuf;
using Google.Protobuf.Collections;

namespace Glide.Protobuf;

public enum ReadFrom
{
    Primary = 0,
    PreferReplica = 1,
    LowestLatency = 2,
    Azaffinity = 3,
    AzaffinityReplicasAndPrimary = 4,
}

public enum TlsMode
{
    NoTls = 0,
    SecureTls = 1,
    InsecureTls = 2,
}

public enum ProtocolVersion
{
    Resp3 = 0,
    Resp2 = 1,
}

public enum CompressionBackend
{
    Zstd = 0,
    Lz4 = 1,
}

public class NodeAddress
{
    public string Host { get; set; } = "";
    public uint Port { get; set; }
}

public class AuthenticationInfo
{
    public string Password { get; set; } = "";
    public string Username { get; set; } = "";
}

public class ConnectionRetryStrategy
{
    public uint NumberOfRetries { get; set; }
    public uint Factor { get; set; }
    public uint ExponentBase { get; set; }
    public uint? JitterPercent { get; set; }
}

public class CompressionConfig
{
    public bool Enabled { get; set; }
    public CompressionBackend Backend { get; set; }
    public int? CompressionLevel { get; set; }
    public uint MinCompressionSize { get; set; }
}
