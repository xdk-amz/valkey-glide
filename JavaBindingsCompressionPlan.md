Here is your task, generate a plan with task checklist in the PLAN section. Update your plan by marking off tasks as you progress, and make commits to the repo with descriptive messages for each task completion

#Task Description:

The transparent compression feature was merged in with only python bindings and requires follow-up PRs to support the other Glide official supported languages. This task tracks the Java implementation.

The transparent compression feature allows users to provide a CompressionConfig specifying a backend, a compression level, an enabled state, and a minimum compression size. Protobuf for the CompressionConfig:

message CompressionConfig {
    bool enabled = 1;
    CompressionBackend backend = 2;
    optional int32 compression_level = 3;
    uint32 min_compression_size = 4;
}
and for the CompressionBackend:

enum CompressionBackend {
    ZSTD = 0;
    LZ4 = 1;
}

Reference Commit with Python and Glide Core implementation: 969fbd342a6db68715af6d2a78bd20c11a662cc2

Requirements:
Implement support for creating and providing a CompressionConfig during client creation
Validate CompressionConfig inputs on creation and return relevant validation errors
Support sync and async client configurations
Write tests covering basic compression functionality, CompressionConfig validation, both backends, and relevant edge cases following the patterns outlined in the existing python compression tests
Implement support for reading the new compression-related statistics and utilize these in the test cases
Include an example file demonstrating client creation with compression configurations

# PLAN

- [ ] 1. Create `CompressionConfiguration` Java config class with builder, validation, and protobuf conversion
- [ ] 2. Add `compressionConfiguration` field to `BaseClientConfiguration` and wire into `ConnectionManager` protobuf serialization
- [ ] 3. Add JNI `getMinCompressedSize` to expose Rust constant and use in Java validation
- [ ] 4. Write integration tests for compression (basic SET/GET, threshold, both backends, batch, validation, disabled-by-default)
- [ ] 5. Create Java compression example file
- [ ] 6. Run lint (`spotlessApply`)

