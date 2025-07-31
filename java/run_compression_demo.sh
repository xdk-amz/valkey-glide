#!/bin/bash

# Script to run the Java compression demo using gradle

echo "🚀 Running Java Compression Demo"
echo "=" $(printf '=%.0s' {1..40})

# Check if Valkey/Redis is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo "❌ Error: Redis/Valkey server not running on localhost:6379"
    echo "Please start a Redis/Valkey server first:"
    echo "  redis-server"
    echo "  # or"
    echo "  valkey-server"
    exit 1
fi

echo "✅ Redis/Valkey server is running"

# Build and run using gradle
echo "🔨 Building and running compression demo..."

# Temporarily change the main class to our demo
sed -i.bak "s/mainClass = 'glide.benchmarks.BenchmarkingApp'/mainClass = 'glide.benchmarks.CompressionDemo'/" benchmarks/build.gradle

# Run the demo
echo "Running CompressionDemo..."
./gradlew :benchmarks:run -q

# Restore the original main class
mv benchmarks/build.gradle.bak benchmarks/build.gradle

echo ""
echo "🎉 Demo completed!"
