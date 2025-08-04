## Run
Ensure that you have a server running on "localhost" on port "6379". To run the ClusterExample, make sure that the server has cluster mode enabled. If the server is running on a different host and/or port, update the StandaloneExample or ClusterExample with a configuration that matches your server settings.

To run the Standalone example:
```
cd valkey-glide/examples/java
./gradlew :runStandalone
```
To run the Cluster example:
```
cd valkey-glide/examples/java
./gradlew :runCluster
```
To run the Compression example:
```
cd valkey-glide/examples/java
./gradlew :runCompression
```

## Examples

- **StandaloneExample.java** - Basic standalone client usage
- **ClusterExample.java** - Basic cluster client usage
- **CompressionExample.java** - Comprehensive compression feature demonstration
- **GlideJsonExample.java** - JSON module usage examples
- **GlideFtExample.java** - Full-text search examples

## Version
These examples are running `valkey-glide` version `1.+`. In order to change the version, update the following section in the `build.gradle` file:
```groovy
dependencies {
    implementation "io.valkey:valkey-glide:1.+:${osdetector.classifier}"
}
```
