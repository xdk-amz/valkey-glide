# Compression Migration Guide

This guide helps you safely migrate existing Valkey GLIDE applications to use automatic compression.

## Overview

The compression feature is designed for seamless migration:

- ✅ **No server changes required** - works with any Redis/Valkey server
- ✅ **No data migration needed** - existing data remains accessible  
- ✅ **Backward compatible** - mixed client scenarios work safely
- ✅ **Rollback friendly** - can disable compression anytime

## Migration Strategies

### Strategy 1: Gradual Client Migration (Recommended)

Migrate clients incrementally to minimize risk:

#### Phase 1: Preparation
1. **Test in staging environment**
2. **Identify candidate applications** (high bandwidth usage, large values)
3. **Establish monitoring** for performance and error rates
4. **Prepare rollback plan**

#### Phase 2: Pilot Deployment
1. **Select low-risk application** for initial deployment
2. **Enable compression with conservative settings**
3. **Monitor for 24-48 hours**
4. **Validate data integrity and performance**

#### Phase 3: Gradual Rollout
1. **Deploy to additional applications** in waves
2. **Monitor each wave** before proceeding
3. **Adjust configuration** based on learnings
4. **Complete migration** once confident

### Strategy 2: Blue-Green Deployment

For applications requiring zero downtime:

#### Blue Environment (Current)
- Existing clients without compression
- Continue serving production traffic

#### Green Environment (New)  
- New clients with compression enabled
- Parallel deployment for testing

#### Migration Process
1. **Deploy green environment** with compression
2. **Route small percentage** of traffic to green
3. **Validate functionality** and performance
4. **Gradually shift traffic** from blue to green
5. **Decommission blue** once migration complete

### Strategy 3: Feature Flag Approach

Use feature flags for controlled rollout:

=== "Python"

    ```python
    import os
    from glide import GlideClientConfiguration, CompressionConfiguration, CompressionBackend

    def create_client_config():
        # Check feature flag
        compression_enabled = os.getenv('COMPRESSION_ENABLED', 'false').lower() == 'true'
        
        config = GlideClientConfiguration(
            addresses=[NodeAddress("localhost", 6379)]
        )
        
        if compression_enabled:
            config.compression = CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=int(os.getenv('COMPRESSION_LEVEL', '3')),
                min_compression_size=int(os.getenv('MIN_COMPRESSION_SIZE', '64'))
            )
        
        return config
    ```

=== "TypeScript"

    ```typescript
    import { GlideClientConfiguration, CompressionConfiguration, CompressionBackend } from "@valkey/valkey-glide";

    function createClientConfig(): GlideClientConfiguration {
        const compressionEnabled = process.env.COMPRESSION_ENABLED === 'true';
        
        const config: GlideClientConfiguration = {
            addresses: [{ host: "localhost", port: 6379 }]
        };
        
        if (compressionEnabled) {
            config.compression = {
                enabled: true,
                backend: CompressionBackend.ZSTD,
                compressionLevel: parseInt(process.env.COMPRESSION_LEVEL || '3'),
                minCompressionSize: parseInt(process.env.MIN_COMPRESSION_SIZE || '64')
            };
        }
        
        return config;
    }
    ```

## Pre-Migration Checklist

### Application Assessment

- [ ] **Identify data patterns**: What types of data does your application store?
- [ ] **Measure value sizes**: What's the typical size distribution of your values?
- [ ] **Analyze traffic patterns**: Which operations are most frequent?
- [ ] **Review performance requirements**: What are your latency/throughput SLAs?
- [ ] **Check error handling**: How does your application handle Redis errors?

### Infrastructure Assessment

- [ ] **Server versions**: Confirm Redis/Valkey server compatibility (any version works)
- [ ] **Network capacity**: Measure current bandwidth usage
- [ ] **Client resources**: Assess CPU/memory capacity for compression overhead
- [ ] **Monitoring setup**: Ensure you can track performance metrics
- [ ] **Backup procedures**: Verify data backup and recovery processes

### Testing Preparation

- [ ] **Staging environment**: Set up environment matching production
- [ ] **Test data**: Prepare representative test dataset
- [ ] **Performance benchmarks**: Establish baseline metrics
- [ ] **Integration tests**: Verify application functionality with compression
- [ ] **Load tests**: Test under production-like load

## Migration Steps

### Step 1: Staging Environment Testing

```python
# Test configuration for staging
staging_compression_config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=1,  # Fast compression for testing
    min_compression_size=32,  # Lower threshold for testing
    max_compression_size=1024*1024  # 1MB limit
)
```

**Testing Checklist:**
- [ ] Basic CRUD operations work correctly
- [ ] Batch operations (pipelines/transactions) function properly
- [ ] Data integrity maintained across operations
- [ ] Performance within acceptable ranges
- [ ] Error handling works as expected
- [ ] Mixed client scenarios work (compressed + uncompressed)

### Step 2: Production Pilot

Select a low-risk application for initial production deployment:

```python
# Conservative production configuration
pilot_compression_config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=3,  # Balanced performance
    min_compression_size=128,  # Skip small values
    max_compression_size=10*1024*1024  # 10MB limit
)
```

**Monitoring Focus:**
- Response time percentiles (P50, P95, P99)
- Error rates and types
- CPU and memory usage
- Network bandwidth reduction
- Compression/decompression success rates

### Step 3: Gradual Rollout

Expand to additional applications in waves:

**Wave 1: Low-risk applications**
- Internal tools
- Non-critical services
- Applications with large, compressible data

**Wave 2: Medium-risk applications**
- Customer-facing services with fallbacks
- Applications with moderate traffic
- Services with good monitoring

**Wave 3: High-risk applications**
- Critical customer-facing services
- High-traffic applications
- Services requiring strict SLAs

### Step 4: Optimization

Fine-tune configuration based on production data:

```python
# Optimized configuration based on learnings
optimized_compression_config = CompressionConfiguration(
    enabled=True,
    backend=CompressionBackend.ZSTD,
    compression_level=2,  # Adjusted based on CPU usage
    min_compression_size=256,  # Adjusted based on size distribution
    max_compression_size=5*1024*1024  # Adjusted based on performance data
)
```

## Monitoring and Validation

### Key Metrics to Track

**Performance Metrics:**
- Request latency (P50, P95, P99)
- Throughput (requests/second)
- CPU utilization
- Memory usage
- Network bandwidth

**Compression Metrics:**
- Compression ratio achieved
- Compression/decompression success rate
- Values compressed vs. skipped
- Error rates by type

**Business Metrics:**
- Application availability
- User experience metrics
- Cost savings (bandwidth, storage)

### Monitoring Setup

=== "Python"

    ```python
    import time
    import logging
    from contextlib import asynccontextmanager

    class CompressionMonitor:
        def __init__(self):
            self.stats = {
                'operations': 0,
                'compression_time': 0,
                'decompression_time': 0,
                'errors': 0
            }
        
        @asynccontextmanager
        async def monitor_operation(self, operation_type):
            start_time = time.time()
            try:
                yield
                self.stats['operations'] += 1
            except Exception as e:
                self.stats['errors'] += 1
                logging.error(f"Compression {operation_type} error: {e}")
                raise
            finally:
                elapsed = time.time() - start_time
                self.stats[f'{operation_type}_time'] += elapsed
        
        def get_stats(self):
            return self.stats.copy()

    # Usage
    monitor = CompressionMonitor()

    async def monitored_set(client, key, value):
        async with monitor.monitor_operation('compression'):
            await client.set(key, value)

    async def monitored_get(client, key):
        async with monitor.monitor_operation('decompression'):
            return await client.get(key)
    ```

=== "TypeScript"

    ```typescript
    class CompressionMonitor {
        private stats = {
            operations: 0,
            compressionTime: 0,
            decompressionTime: 0,
            errors: 0
        };

        async monitorOperation<T>(operationType: string, operation: () => Promise<T>): Promise<T> {
            const startTime = Date.now();
            try {
                const result = await operation();
                this.stats.operations++;
                return result;
            } catch (error) {
                this.stats.errors++;
                console.error(`Compression ${operationType} error:`, error);
                throw error;
            } finally {
                const elapsed = Date.now() - startTime;
                this.stats[`${operationType}Time` as keyof typeof this.stats] += elapsed;
            }
        }

        getStats() {
            return { ...this.stats };
        }
    }

    // Usage
    const monitor = new CompressionMonitor();

    async function monitoredSet(client: GlideClient, key: string, value: string) {
        return monitor.monitorOperation('compression', () => client.set(key, value));
    }

    async function monitoredGet(client: GlideClient, key: string) {
        return monitor.monitorOperation('decompression', () => client.get(key));
    }
    ```

### Alerting Setup

Set up alerts for critical metrics:

```yaml
# Example Prometheus alerting rules
groups:
  - name: compression_alerts
    rules:
      - alert: CompressionErrorRateHigh
        expr: compression_error_rate > 0.01  # 1% error rate
        for: 5m
        annotations:
          summary: "High compression error rate detected"
          
      - alert: CompressionLatencyHigh
        expr: compression_latency_p95 > 10  # 10ms P95 latency
        for: 5m
        annotations:
          summary: "High compression latency detected"
          
      - alert: CompressionRatioLow
        expr: compression_ratio < 0.1  # Less than 10% compression
        for: 15m
        annotations:
          summary: "Low compression ratio - review configuration"
```

## Rollback Procedures

### Emergency Rollback

If issues arise, quickly disable compression:

=== "Python"

    ```python
    # Emergency rollback - disable compression
    emergency_config = GlideClientConfiguration(
        addresses=[NodeAddress("localhost", 6379)],
        compression=CompressionConfiguration(enabled=False)
    )
    
    # Restart clients with new configuration
    client = await GlideClient.create(emergency_config)
    ```

=== "TypeScript"

    ```typescript
    // Emergency rollback - disable compression
    const emergencyConfig = {
        addresses: [{ host: "localhost", port: 6379 }],
        compression: { enabled: false }
    };
    
    // Restart clients with new configuration
    const client = await GlideClient.createClient(emergencyConfig);
    ```

### Gradual Rollback

For planned rollback, reverse the migration process:

1. **Stop new deployments** with compression
2. **Monitor existing** compressed clients
3. **Gradually replace** with non-compression clients
4. **Validate** that compressed data is still accessible
5. **Complete rollback** once all clients updated

### Data Considerations

**Important:** Rollback doesn't affect data integrity:

- Compressed data remains in Redis/Valkey
- Non-compression clients will see raw compressed bytes
- Re-enabling compression will restore normal operation
- No data loss occurs during rollback

## Common Migration Scenarios

### Scenario 1: High-Traffic Web Application

**Challenge:** Minimize performance impact during migration

**Solution:**
```python
# Start with minimal compression
initial_config = CompressionConfiguration(
    enabled=True,
    compression_level=1,  # Fastest compression
    min_compression_size=1024,  # Only large values
    max_compression_size=100*1024  # Limit max size
)

# Gradually optimize
optimized_config = CompressionConfiguration(
    enabled=True,
    compression_level=3,  # Better compression
    min_compression_size=256,  # More values
    max_compression_size=1024*1024  # Higher limit
)
```

### Scenario 2: Microservices Architecture

**Challenge:** Coordinate migration across multiple services

**Solution:**
1. **Service dependency mapping** - identify data flow between services
2. **Staged migration** - migrate data producers before consumers
3. **Version compatibility** - ensure services can handle both formats
4. **Centralized configuration** - use config service for compression settings

### Scenario 3: Multi-Region Deployment

**Challenge:** Coordinate migration across regions

**Solution:**
1. **Region-by-region migration** - complete one region before next
2. **Cross-region data compatibility** - ensure compressed data works across regions
3. **Monitoring per region** - track metrics separately
4. **Rollback coordination** - plan for region-specific rollbacks

## Best Practices

### Configuration Management

- **Use environment variables** for compression settings
- **Version control** compression configurations
- **Document changes** and rationale
- **Test configuration changes** in staging first

### Monitoring and Alerting

- **Establish baselines** before migration
- **Monitor continuously** during migration
- **Set up alerts** for key metrics
- **Review metrics regularly** and adjust as needed

### Team Coordination

- **Communicate migration plan** to all stakeholders
- **Train team members** on compression features
- **Document procedures** for troubleshooting
- **Plan for 24/7 support** during critical phases

### Risk Mitigation

- **Start with low-risk applications**
- **Have rollback plan ready**
- **Test thoroughly** in staging
- **Monitor closely** during migration
- **Keep team available** for quick response

## Post-Migration

### Optimization

After successful migration:

1. **Analyze compression effectiveness** by data type
2. **Fine-tune configuration** based on production data
3. **Consider advanced features** as they become available
4. **Document lessons learned** for future migrations

### Maintenance

Ongoing maintenance tasks:

- **Monitor compression metrics** regularly
- **Update configurations** as data patterns change
- **Review performance** periodically
- **Plan for future enhancements**

## Troubleshooting Migration Issues

### Common Issues

**Issue:** Performance degradation after enabling compression
- **Solution:** Lower compression level or increase size thresholds

**Issue:** Increased error rates
- **Solution:** Check data types and compression compatibility

**Issue:** Memory usage increase
- **Solution:** Adjust max compression size or compression level

**Issue:** Cross-service compatibility problems
- **Solution:** Ensure all services use compatible compression settings

### Getting Help

For migration support:

- Review [Compression Troubleshooting Guide](compression-troubleshooting.md)
- Check [GitHub Issues](https://github.com/valkey-io/valkey-glide/issues)
- Join [Community Discussions](https://github.com/valkey-io/valkey-glide/discussions)

## Success Metrics

Measure migration success by:

- **Bandwidth reduction** (target: 30-70% depending on data)
- **Storage savings** (varies by data compressibility)
- **Performance impact** (target: <5% latency increase)
- **Error rate** (target: <0.1% compression errors)
- **Availability** (maintain existing SLAs)

A successful migration achieves significant bandwidth/storage savings while maintaining application performance and reliability.
