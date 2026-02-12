# C# Examples

## Compression Example

Demonstrates how to create GLIDE clients with compression configurations.

### Features Shown
- Standalone client with ZSTD compression
- Cluster client with LZ4 compression
- Using backend default compression levels
- Setting compression after config creation
- Protobuf serialization for FFI
- Reading compression statistics

### Running

```bash
# From the examples/csharp directory
dotnet run --project ../../csharp/lib CompressionExample.cs
```

Or reference the Glide library project and run directly:

```bash
dotnet script CompressionExample.cs
```
