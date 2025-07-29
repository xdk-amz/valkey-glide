# C# Examples

This directory contains examples demonstrating how to use Valkey GLIDE with C#.

## Prerequisites

- .NET 6.0 or later
- A running Redis/Valkey server

## Examples

- **CompressionExample.cs** - Comprehensive compression feature demonstration

## Run

To run the compression example:

```bash
cd examples/csharp
dotnet run CompressionExample.cs
```

Make sure you have a Redis/Valkey server running on localhost:6379, or update the connection configuration in the examples to match your server settings.

## Features Demonstrated

The compression example shows:

- Basic compression configuration and usage
- Different compression settings for various use cases
- Batch operations with compression (pipelines and transactions)
- Mixed client scenarios (compression-enabled and disabled clients)
- Performance comparison with and without compression
- Error handling and graceful fallback
- Cluster client usage with compression

## Configuration Examples

The examples demonstrate various compression configurations:

- **Development**: Fast compression with lower thresholds
- **Production Balanced**: Good balance of speed and compression ratio
- **High Performance**: Optimized for speed
- **Storage Optimized**: Optimized for maximum compression

Each configuration is suitable for different use cases and performance requirements.
