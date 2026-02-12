# C# Examples

## Compression Example

Demonstrates how to configure GLIDE clients with compression and shows the intended
usage pattern for SET/GET with statistics verification.

### Features Shown
- Standalone client with ZSTD compression
- Cluster client with LZ4 compression
- Backend default compression levels
- Backend mismatch (ZSTD writer, LZ4 reader)
- Disabled compression
- Reading compression statistics
- Protobuf serialization for FFI

### Current Status

The configuration, statistics, and protobuf serialization code runs today.
The actual SET/GET operations and statistics verification are commented out with
TODO markers — they require the full C# client FFI wiring (`GlideClient.CreateAsync`,
`SetAsync`, `GetAsync`, `GetStatisticsAsync`) to be complete.

### Running

The example requires a project reference to the Glide library:

```bash
# From the repository root
dotnet run --project csharp/lib -- examples/csharp/CompressionExample.cs
```

Or add a project reference and run as a standalone console app:

```bash
# Create a new console project, add reference, then copy the example
dotnet new console -o examples/csharp/runner
dotnet add examples/csharp/runner reference csharp/lib/Glide.csproj
cp examples/csharp/CompressionExample.cs examples/csharp/runner/Program.cs
dotnet run --project examples/csharp/runner
```
