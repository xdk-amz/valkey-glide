### Install node 16 (or newer)
```
curl -s https://deb.nodesource.com/setup_16.x | sudo bash
apt-get install nodejs npm
npm i -g npm@8
```

## Install GLIDE package and build the example
```
cd valkey-glide/examples/node
npm install
npx tsc
```

## Run
To run the examples (make sure redis/valkey server is available at the address used in the example):
```
cd valkey-glide/examples/node
node index.js
node compression_example.js
```

## Examples

- **index.ts** - Basic client usage examples
- **standalone_example.ts** - Standalone client example
- **cluster_example.ts** - Cluster client example
- **compression_example.ts** - Comprehensive compression feature demonstration
- **json_example.ts** - JSON module usage examples
- **vector_search_example.ts** - Vector search examples
