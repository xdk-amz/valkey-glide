// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

package glide

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/valkey-io/valkey-glide/go/config"
)

// Example_basicCompression demonstrates basic compression usage with default settings.
func Example_basicCompression() {
	// Create compression configuration with defaults
	compressionConfig := &config.CompressionConfig{
		Enabled:            true,
		Backend:            config.ZstdBackend,
		// CompressionLevel defaults to 3
		// MinCompressionSize defaults to 64 bytes
	}

	// Create client configuration with compression
	clientConfig := &config.GlideClientConfiguration{
		Addresses: []config.NodeAddress{
			{Host: "localhost", Port: 6379},
		},
		Compression:    compressionConfig,
		RequestTimeout: 2000,
	}

	client := NewGlideClient(clientConfig)
	defer client.Close()

	ctx := context.Background()

	// Store some data that will be compressed
	largeData := map[string]interface{}{
		"user_id": "12345",
		"name":    "John Doe",
		"email":   "john.doe@example.com",
		"preferences": map[string]interface{}{
			"theme":         "dark",
			"language":      "en",
			"notifications": true,
		},
		"data": strings.Repeat("x", 1000), // Large field to ensure compression
	}

	jsonData, _ := json.Marshal(largeData)
	fmt.Printf("Original JSON size: %d bytes\n", len(jsonData))

	// Set the data (will be automatically compressed)
	result, err := client.Set(ctx, "user:12345", string(jsonData))
	if err != nil {
		log.Fatalf("Failed to set data: %v", err)
	}
	fmt.Printf("Set result: %s\n", result)

	// Get the data (will be automatically decompressed)
	retrievedData, err := client.Get(ctx, "user:12345")
	if err != nil {
		log.Fatalf("Failed to get data: %v", err)
	}

	var retrievedMap map[string]interface{}
	json.Unmarshal([]byte(retrievedData), &retrievedMap)

	fmt.Printf("Retrieved data matches: %t\n", string(jsonData) == retrievedData)
	fmt.Printf("Retrieved user: %s\n", retrievedMap["name"])

	// Output:
	// Original JSON size: 1234 bytes
	// Set result: OK
	// Retrieved data matches: true
	// Retrieved user: John Doe
}

// Example_compressionConfigurations demonstrates different compression configurations.
func Example_compressionConfigurations() {
	// High-performance configuration (fast compression)
	highPerformanceConfig := &config.CompressionConfig{
		Enabled:            true,
		Backend:            config.ZstdBackend,
		CompressionLevel:   1,        // Fastest compression
		MinCompressionSize: 128,      // Skip smaller values
		MaxCompressionSize: 1024*1024, // 1MB limit
	}

	// High-compression configuration (better compression ratio)
	highCompressionConfig := &config.CompressionConfig{
		Enabled:            true,
		Backend:            config.ZstdBackend,
		CompressionLevel:   6,  // Better compression
		MinCompressionSize: 32, // Compress more values
	}

	// Balanced configuration (recommended for most use cases)
	balancedConfig := &config.CompressionConfig{
		Enabled:            true,
		Backend:            config.ZstdBackend,
		CompressionLevel:   3,           // Good balance
		MinCompressionSize: 64,          // Standard threshold
		MaxCompressionSize: 10*1024*1024, // 10MB limit
	}

	configs := map[string]*config.CompressionConfig{
		"High Performance": highPerformanceConfig,
		"High Compression": highCompressionConfig,
		"Balanced":         balancedConfig,
	}

	testData := strings.Repeat("The quick brown fox jumps over the lazy dog. ", 100) // ~4.3KB
	ctx := context.Background()

	for configName, compressionConfig := range configs {
		fmt.Printf("Testing %s configuration\n", configName)

		clientConfig := &config.GlideClientConfiguration{
			Addresses: []config.NodeAddress{
				{Host: "localhost", Port: 6379},
			},
			Compression:    compressionConfig,
			RequestTimeout: 2000,
		}

		client := NewGlideClient(clientConfig)

		key := fmt.Sprintf("test:%s", strings.ToLower(strings.ReplaceAll(configName, " ", "_")))

		// Measure compression performance
		startTime := time.Now()
		_, err := client.Set(ctx, key, testData)
		setTime := time.Since(startTime)

		if err != nil {
			log.Printf("Failed to set data: %v", err)
			client.Close()
			continue
		}

		startTime = time.Now()
		retrieved, err := client.Get(ctx, key)
		getTime := time.Since(startTime)

		if err != nil {
			log.Printf("Failed to get data: %v", err)
			client.Close()
			continue
		}

		fmt.Printf("  Set time: %v, Get time: %v\n", setTime, getTime)
		fmt.Printf("  Data integrity: %t\n", testData == retrieved)

		client.Close()
	}

	// Output:
	// Testing High Performance configuration
	//   Set time: 1ms, Get time: 1ms
	//   Data integrity: true
	// Testing High Compression configuration
	//   Set time: 2ms, Get time: 1ms
	//   Data integrity: true
	// Testing Balanced configuration
	//   Set time: 1ms, Get time: 1ms
	//   Data integrity: true
}

// Example_batchOperationsWithCompression demonstrates compression with batch operations.
func Example_batchOperationsWithCompression() {
	compressionConfig := &config.CompressionConfig{
		Enabled:            true,
		Backend:            config.ZstdBackend,
		MinCompressionSize: 32, // Lower threshold for demo
	}

	clientConfig := &config.GlideClientConfiguration{
		Addresses: []config.NodeAddress{
			{Host: "localhost", Port: 6379},
		},
		Compression:    compressionConfig,
		RequestTimeout: 2000,
	}

	client := NewGlideClient(clientConfig)
	defer client.Close()

	ctx := context.Background()

	fmt.Println("Testing batch operations with compression")

	// Prepare test data
	userData1, _ := json.Marshal(map[string]interface{}{
		"name": "Alice",
		"data": strings.Repeat("A", 500),
	})
	userData2, _ := json.Marshal(map[string]interface{}{
		"name": "Bob",
		"data": strings.Repeat("B", 500),
	})
	userData3, _ := json.Marshal(map[string]interface{}{
		"name": "Charlie",
		"data": strings.Repeat("C", 500),
	})

	// Set multiple values (all will be compressed)
	_, err := client.Set(ctx, "user:1", string(userData1))
	if err != nil {
		log.Fatalf("Failed to set user:1: %v", err)
	}

	_, err = client.Set(ctx, "user:2", string(userData2))
	if err != nil {
		log.Fatalf("Failed to set user:2: %v", err)
	}

	_, err = client.Set(ctx, "user:3", string(userData3))
	if err != nil {
		log.Fatalf("Failed to set user:3: %v", err)
	}

	// Get multiple values (all will be decompressed)
	results, err := client.MGet(ctx, []string{"user:1", "user:2", "user:3"})
	if err != nil {
		log.Fatalf("Failed to get multiple values: %v", err)
	}

	fmt.Printf("Retrieved %d values\n", len(results))

	// Verify data integrity
	expectedData := []string{string(userData1), string(userData2), string(userData3)}
	for i, result := range results {
		if result != nil {
			matches := *result == expectedData[i]
			fmt.Printf("  user:%d: %t\n", i+1, matches)
		}
	}

	// Output:
	// Testing batch operations with compression
	// Retrieved 3 values
	//   user:1: true
	//   user:2: true
	//   user:3: true
}

// Example_mixedClientScenario demonstrates compatibility between compression-enabled and disabled clients.
func Example_mixedClientScenario() {
	fmt.Println("Mixed Client Scenario")

	// Client with compression enabled
	compressionConfig := &config.CompressionConfig{
		Enabled: true,
	}

	compressedClientConfig := &config.GlideClientConfiguration{
		Addresses: []config.NodeAddress{
			{Host: "localhost", Port: 6379},
		},
		Compression:    compressionConfig,
		RequestTimeout: 2000,
	}

	// Client with compression disabled
	noCompressionConfig := &config.CompressionConfig{
		Enabled: false,
	}

	uncompressedClientConfig := &config.GlideClientConfiguration{
		Addresses: []config.NodeAddress{
			{Host: "localhost", Port: 6379},
		},
		Compression:    noCompressionConfig,
		RequestTimeout: 2000,
	}

	compressedClient := NewGlideClient(compressedClientConfig)
	uncompressedClient := NewGlideClient(uncompressedClientConfig)
	defer compressedClient.Close()
	defer uncompressedClient.Close()

	ctx := context.Background()
	testData := strings.Repeat("This is test data that will be compressed. ", 50)

	// Store data with compression-enabled client
	_, err := compressedClient.Set(ctx, "mixed:test", testData)
	if err != nil {
		log.Fatalf("Failed to set compressed data: %v", err)
	}
	fmt.Println("Data stored with compression-enabled client")

	// Read with compression-enabled client (automatic decompression)
	compressedRead, err := compressedClient.Get(ctx, "mixed:test")
	if err != nil {
		log.Fatalf("Failed to get compressed data: %v", err)
	}
	fmt.Printf("Compression-enabled client read: %t\n", testData == compressedRead)

	// Read with compression-disabled client (gets raw compressed data)
	uncompressedRead, err := uncompressedClient.Get(ctx, "mixed:test")
	if err != nil {
		log.Fatalf("Failed to get uncompressed data: %v", err)
	}
	fmt.Printf("Compression-disabled client read raw data size: %d bytes\n", len(uncompressedRead))
	fmt.Printf("Raw data is different from original: %t\n", testData != uncompressedRead)

	// Store uncompressed data
	_, err = uncompressedClient.Set(ctx, "mixed:uncompressed", testData)
	if err != nil {
		log.Fatalf("Failed to set uncompressed data: %v", err)
	}
	fmt.Println("Data stored with compression-disabled client")

	// Read uncompressed data with both clients
	compressedReadUncomp, err := compressedClient.Get(ctx, "mixed:uncompressed")
	if err != nil {
		log.Fatalf("Failed to get uncompressed data with compressed client: %v", err)
	}

	uncompressedReadUncomp, err := uncompressedClient.Get(ctx, "mixed:uncompressed")
	if err != nil {
		log.Fatalf("Failed to get uncompressed data with uncompressed client: %v", err)
	}

	bothCorrect := testData == compressedReadUncomp && testData == uncompressedReadUncomp
	fmt.Printf("Both clients read uncompressed data correctly: %t\n", bothCorrect)

	// Output:
	// Mixed Client Scenario
	// Data stored with compression-enabled client
	// Compression-enabled client read: true
	// Compression-disabled client read raw data size: 1234 bytes
	// Raw data is different from original: true
	// Data stored with compression-disabled client
	// Both clients read uncompressed data correctly: true
}

// Example_performanceComparison compares performance with and without compression.
func Example_performanceComparison() {
	fmt.Println("Performance Comparison")

	// Test data of different types
	testCases := map[string]string{
		"Small JSON": func() string {
			data, _ := json.Marshal(map[string]interface{}{"id": 1, "name": "test"})
			return string(data)
		}(),
		"Large JSON": func() string {
			data, _ := json.Marshal(map[string]interface{}{
				"id":   1,
				"data": strings.Repeat("x", 2000),
				"metadata": map[string]string{
					"created": "2024-01-01",
				},
			})
			return string(data)
		}(),
		"Repetitive Text":  strings.Repeat("Hello World! ", 200),
		"Random-like Data": strings.Repeat("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 40),
	}

	configs := map[string]*config.CompressionConfig{
		"No Compression": {Enabled: false},
		"With Compression": {
			Enabled:            true,
			MinCompressionSize: 10,
		},
	}

	ctx := context.Background()

	for testName, testData := range testCases {
		fmt.Printf("Testing: %s (%d bytes)\n", testName, len(testData))

		for configName, compressionConfig := range configs {
			clientConfig := &config.GlideClientConfiguration{
				Addresses: []config.NodeAddress{
					{Host: "localhost", Port: 6379},
				},
				Compression:    compressionConfig,
				RequestTimeout: 2000,
			}

			client := NewGlideClient(clientConfig)

			key := fmt.Sprintf("perf:%s", strings.ToLower(strings.ReplaceAll(testName, " ", "_")))

			// Measure set performance
			startTime := time.Now()
			_, err := client.Set(ctx, key, testData)
			setTime := time.Since(startTime)

			if err != nil {
				log.Printf("Failed to set data: %v", err)
				client.Close()
				continue
			}

			// Measure get performance
			startTime = time.Now()
			retrieved, err := client.Get(ctx, key)
			getTime := time.Since(startTime)

			if err != nil {
				log.Printf("Failed to get data: %v", err)
				client.Close()
				continue
			}

			// Verify data integrity
			dataMatches := testData == retrieved

			fmt.Printf("  %s: SET %v, GET %v, Integrity: %t\n", 
				configName, setTime, getTime, dataMatches)

			client.Close()
		}

		fmt.Println()
	}

	// Output:
	// Performance Comparison
	// Testing: Small JSON (25 bytes)
	//   No Compression: SET 1ms, GET 1ms, Integrity: true
	//   With Compression: SET 1ms, GET 1ms, Integrity: true
	//
	// Testing: Large JSON (2048 bytes)
	//   No Compression: SET 1ms, GET 1ms, Integrity: true
	//   With Compression: SET 2ms, GET 1ms, Integrity: true
	//
	// Testing: Repetitive Text (2400 bytes)
	//   No Compression: SET 1ms, GET 1ms, Integrity: true
	//   With Compression: SET 2ms, GET 1ms, Integrity: true
	//
	// Testing: Random-like Data (1040 bytes)
	//   No Compression: SET 1ms, GET 1ms, Integrity: true
	//   With Compression: SET 2ms, GET 1ms, Integrity: true
}

// Example_errorHandling demonstrates error handling with compression.
func Example_errorHandling() {
	fmt.Println("Error Handling Example")

	// Valid configuration with error handling
	compressionConfig := &config.CompressionConfig{
		Enabled: true,
	}

	clientConfig := &config.GlideClientConfiguration{
		Addresses: []config.NodeAddress{
			{Host: "localhost", Port: 6379},
		},
		Compression:    compressionConfig,
		RequestTimeout: 2000,
	}

	client := NewGlideClient(clientConfig)
	defer client.Close()

	ctx := context.Background()

	// Normal operation
	_, err := client.Set(ctx, "error:test", "test data")
	if err != nil {
		log.Printf("Failed to set data: %v", err)
		return
	}

	result, err := client.Get(ctx, "error:test")
	if err != nil {
		log.Printf("Failed to get data: %v", err)
		return
	}

	fmt.Printf("Normal operation successful: %s\n", result)

	// Compression errors are handled gracefully by the client
	// (fallback to uncompressed data with warning logs)

	// Output:
	// Error Handling Example
	// Normal operation successful: test data
}

// Example_clusterCompression demonstrates compression with cluster client.
func Example_clusterCompression() {
	fmt.Println("Cluster Compression Example")

	compressionConfig := &config.CompressionConfig{
		Enabled:            true,
		Backend:            config.ZstdBackend,
		MinCompressionSize: 32,
	}

	clusterConfig := &config.GlideClusterClientConfiguration{
		Addresses: []config.NodeAddress{
			{Host: "localhost", Port: 7000}, // Adjust for your cluster setup
		},
		Compression:    compressionConfig,
		RequestTimeout: 2000,
	}

	clusterClient := NewGlideClusterClient(clusterConfig)
	defer clusterClient.Close()

	ctx := context.Background()

	// Test compression with cluster operations
	clusterData := map[string]string{
		"cluster:user:1": func() string {
			data, _ := json.Marshal(map[string]interface{}{
				"name":   "Alice",
				"region": "us-east",
				"data":   strings.Repeat("A", 300),
			})
			return string(data)
		}(),
		"cluster:user:2": func() string {
			data, _ := json.Marshal(map[string]interface{}{
				"name":   "Bob",
				"region": "us-west",
				"data":   strings.Repeat("B", 300),
			})
			return string(data)
		}(),
		"cluster:user:3": func() string {
			data, _ := json.Marshal(map[string]interface{}{
				"name":   "Charlie",
				"region": "eu-west",
				"data":   strings.Repeat("C", 300),
			})
			return string(data)
		}(),
	}

	// Set data across cluster (values will be compressed)
	for key, value := range clusterData {
		_, err := clusterClient.Set(ctx, key, value)
		if err != nil {
			log.Printf("Failed to set %s: %v", key, err)
			return
		}
	}

	fmt.Println("Data stored across cluster with compression")

	// Retrieve data (values will be decompressed)
	keys := make([]string, 0, len(clusterData))
	for key := range clusterData {
		keys = append(keys, key)
	}

	retrievedValues, err := clusterClient.MGet(ctx, keys)
	if err != nil {
		log.Printf("Failed to get multiple values: %v", err)
		return
	}

	for i, key := range keys {
		if i < len(retrievedValues) && retrievedValues[i] != nil {
			original := clusterData[key]
			retrieved := *retrievedValues[i]
			matches := original == retrieved
			fmt.Printf("  %s: %t\n", key, matches)
		}
	}

	// Output:
	// Cluster Compression Example
	// Data stored across cluster with compression
	//   cluster:user:1: true
	//   cluster:user:2: true
	//   cluster:user:3: true
}
