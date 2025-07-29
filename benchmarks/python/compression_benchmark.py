# Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

import argparse
import functools
import json
import math
import random
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from statistics import mean
from typing import List

import anyio
import numpy as np
import redis.asyncio as redispy  # type: ignore
from glide import (
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    Logger,
    LogLevel,
    NodeAddress,
    CompressionConfiguration,
    CompressionBackend,
)


class ChosenAction(Enum):
    GET_NON_EXISTING = 1
    GET_EXISTING = 2
    SET = 3


PORT = 6379

arguments_parser = argparse.ArgumentParser()
arguments_parser.add_argument(
    "--resultsFile",
    help="Where to write the results file",
    required=False,
    default="../results/python-compression-results.json",
)
arguments_parser.add_argument(
    "--dataSize", help="Size of data to set", required=False, default="1000"
)
arguments_parser.add_argument(
    "--concurrentTasks",
    help="List of number of concurrent tasks to run",
    nargs="+",
    required=False,
    default=("10", "100"),
)
arguments_parser.add_argument(
    "--host", help="What host to target", required=False, default="localhost"
)
arguments_parser.add_argument(
    "--clientCount",
    help="Number of clients to run concurrently",
    nargs="+",
    required=False,
    default=("1"),
)
arguments_parser.add_argument(
    "--tls",
    help="Should benchmark a TLS server",
    action="store_true",
    required=False,
    default=False,
)
arguments_parser.add_argument(
    "--clusterModeEnabled",
    help="Should benchmark a cluster mode enabled cluster",
    action="store_true",
    required=False,
    default=False,
)
arguments_parser.add_argument(
    "--port",
    default=PORT,
    type=int,
    required=False,
    help="Which port to connect to, defaults to `%(default)s`",
)
arguments_parser.add_argument(
    "--minimal", help="Should run a minimal benchmark", action="store_true"
)
arguments_parser.add_argument(
    "--backend",
    help="Async backend to use",
    required=False,
    default="asyncio",
    choices=["asyncio", "trio"],
)
arguments_parser.add_argument(
    "--compressionBackend",
    help="Compression backend to use",
    required=False,
    default="zstd",
    choices=["zstd", "lz4"],
)
arguments_parser.add_argument(
    "--compressionLevel",
    help="Compression level (1-22 for ZSTD, 1-12 for LZ4)",
    type=int,
    required=False,
    default=3,
)
arguments_parser.add_argument(
    "--minCompressionSize",
    help="Minimum size in bytes for compression",
    type=int,
    required=False,
    default=64,
)
args = arguments_parser.parse_args()

if args.backend == "trio":
    raise ValueError("Trio backend is only supported on the 'glide' client")

PROB_GET = 0.8
PROB_GET_EXISTING_KEY = 0.8
SIZE_GET_KEYSPACE = 3750000  # 3.75 million
SIZE_SET_KEYSPACE = 3000000  # 3 million
started_tasks_counter = 0
bench_json_results: List[str] = []


def truncate_decimal(number: float, digits: int = 3) -> float:
    stepper = 10**digits
    return math.floor(number * stepper) / stepper


def generate_value(size):
    # Generate compressible data (repeated patterns)
    pattern = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    repetitions = max(1, size // len(pattern))
    remainder = size % len(pattern)
    return (pattern * repetitions + pattern[:remainder])[:size]


def generate_key_set():
    return str(random.randint(1, SIZE_SET_KEYSPACE + 1))


def generate_key_get():
    return str(random.randint(SIZE_SET_KEYSPACE, SIZE_GET_KEYSPACE + 1))


def choose_action():
    if random.random() > PROB_GET:
        return ChosenAction.SET
    if random.random() > PROB_GET_EXISTING_KEY:
        return ChosenAction.GET_NON_EXISTING
    return ChosenAction.GET_EXISTING


def calculate_latency(latency_list, percentile):
    return round(np.percentile(np.array(latency_list), percentile), 4)


def process_results():
    global bench_json_results
    global args

    # write json results to a file
    res_file_path = args.resultsFile
    with open(res_file_path, "w+") as f:
        json.dump(bench_json_results, f, indent=2)


def timer(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        await func(*args, **kwargs)
        toc = time.perf_counter()
        return toc - tic

    return wrapper


async def execute_commands(clients, total_commands, data_size, action_latencies):
    global started_tasks_counter
    while started_tasks_counter < total_commands:
        started_tasks_counter += 1
        chosen_action = choose_action()
        client = clients[started_tasks_counter % len(clients)]
        tic = time.perf_counter()
        if chosen_action == ChosenAction.GET_EXISTING:
            await client.get(generate_key_set())
        elif chosen_action == ChosenAction.GET_NON_EXISTING:
            await client.get(generate_key_get())
        elif chosen_action == ChosenAction.SET:
            await client.set(generate_key_set(), generate_value(data_size))
        toc = time.perf_counter()
        execution_time_milli = (toc - tic) * 1000
        action_latencies[chosen_action].append(truncate_decimal(execution_time_milli))
    return True


@timer
async def create_and_run_concurrent_tasks(
    clients, total_commands, num_of_concurrent_tasks, data_size, action_latencies
):
    global started_tasks_counter
    started_tasks_counter = 0

    async with anyio.create_task_group() as tg:
        for _ in range(num_of_concurrent_tasks):
            tg.start_soon(
                execute_commands,
                clients,
                total_commands,
                data_size,
                action_latencies,
            )


def latency_results(prefix, latencies):
    result = {}
    result[prefix + "_p50_latency"] = calculate_latency(latencies, 50)
    result[prefix + "_p90_latency"] = calculate_latency(latencies, 90)
    result[prefix + "_p99_latency"] = calculate_latency(latencies, 99)
    result[prefix + "_average_latency"] = truncate_decimal(mean(latencies))
    result[prefix + "_std_dev"] = truncate_decimal(np.std(latencies))

    return result


async def create_clients(client_count, action):
    return [await action() for _ in range(client_count)]


async def run_clients(
    clients,
    client_name,
    event_loop_name,
    total_commands,
    num_of_concurrent_tasks,
    data_size,
    is_cluster,
    compression_enabled=False,
    compression_backend=None,
    compression_level=None,
    min_compression_size=None,
):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    compression_info = ""
    if compression_enabled:
        compression_info = f" compression: {compression_backend} level {compression_level}"
    
    print(
        f"Starting {client_name} data size: {data_size} concurrency:"
        f"{num_of_concurrent_tasks} client count: {len(clients)}{compression_info} {now}"
    )
    action_latencies = {
        ChosenAction.GET_NON_EXISTING: list(),
        ChosenAction.GET_EXISTING: list(),
        ChosenAction.SET: list(),
    }
    time = await create_and_run_concurrent_tasks(
        clients, total_commands, num_of_concurrent_tasks, data_size, action_latencies
    )
    tps = int(started_tasks_counter / time)
    get_non_existing_latencies = action_latencies[ChosenAction.GET_NON_EXISTING]
    get_non_existing_latency_results = latency_results(
        "get_non_existing", get_non_existing_latencies
    )

    get_existing_latencies = action_latencies[ChosenAction.GET_EXISTING]
    get_existing_latency_results = latency_results(
        "get_existing", get_existing_latencies
    )

    set_latencies = action_latencies[ChosenAction.SET]
    set_results = latency_results("set", set_latencies)

    json_res = {
        **{
            "client": client_name,
            "loop": event_loop_name,
            "num_of_tasks": num_of_concurrent_tasks,
            "data_size": data_size,
            "tps": tps,
            "client_count": len(clients),
            "is_cluster": is_cluster,
            "compression_enabled": compression_enabled,
            "compression_backend": compression_backend,
            "compression_level": compression_level,
            "min_compression_size": min_compression_size,
        },
        **get_existing_latency_results,
        **get_non_existing_latency_results,
        **set_results,
    }

    bench_json_results.append(json_res)


async def main(
    event_loop_name,
    total_commands,
    num_of_concurrent_tasks,
    data_size,
    host,
    client_count,
    use_tls,
    is_cluster,
    compression_backend,
    compression_level,
    min_compression_size,
):
    # Test without compression first
    client_class = GlideClusterClient if is_cluster else GlideClient
    config = (
        GlideClusterClientConfiguration(
            [NodeAddress(host=host, port=port)], use_tls=use_tls
        )
        if is_cluster
        else GlideClientConfiguration(
            [NodeAddress(host=host, port=port)], use_tls=use_tls
        )
    )
    clients = await create_clients(
        client_count,
        lambda: client_class.create(config),
    )
    await run_clients(
        clients,
        "glide-no-compression",
        event_loop_name,
        total_commands,
        num_of_concurrent_tasks,
        data_size,
        is_cluster,
        compression_enabled=False,
    )
    
    # Close clients
    for client in clients:
        await client.close()

    # Test with compression
    backend = CompressionBackend.ZSTD if compression_backend == "zstd" else CompressionBackend.LZ4
    compression_config = CompressionConfiguration(
        enabled=True,
        backend=backend,
        compression_level=compression_level,
        min_compression_size=min_compression_size,
    )
    
    config_with_compression = (
        GlideClusterClientConfiguration(
            [NodeAddress(host=host, port=port)], 
            use_tls=use_tls,
            compression=compression_config
        )
        if is_cluster
        else GlideClientConfiguration(
            [NodeAddress(host=host, port=port)], 
            use_tls=use_tls,
            compression=compression_config
        )
    )
    
    clients_with_compression = await create_clients(
        client_count,
        lambda: client_class.create(config_with_compression),
    )
    
    await run_clients(
        clients_with_compression,
        "glide-with-compression",
        event_loop_name,
        total_commands,
        num_of_concurrent_tasks,
        data_size,
        is_cluster,
        compression_enabled=True,
        compression_backend=compression_backend,
        compression_level=compression_level,
        min_compression_size=min_compression_size,
    )
    
    # Close clients
    for client in clients_with_compression:
        await client.close()


def number_of_iterations(num_of_concurrent_tasks):
    return min(max(10000, num_of_concurrent_tasks * 1000), 100000)


if __name__ == "__main__":
    concurrent_tasks = args.concurrentTasks
    data_size = int(args.dataSize)
    client_count = args.clientCount
    host = args.host
    use_tls = args.tls
    port = args.port
    is_cluster = args.clusterModeEnabled
    compression_backend = args.compressionBackend
    compression_level = args.compressionLevel
    min_compression_size = args.minCompressionSize

    # Setting the internal logger to log every log that has a level of info and above,
    # and save the logs to a file with the name of the results file.
    Logger.set_logger_config(LogLevel.INFO, Path(args.resultsFile).stem)

    product_of_arguments = [
        (data_size, int(num_of_concurrent_tasks), int(number_of_clients))
        for num_of_concurrent_tasks in concurrent_tasks
        for number_of_clients in client_count
        if int(number_of_clients) <= int(num_of_concurrent_tasks)
    ]

    for data_size, num_of_concurrent_tasks, number_of_clients in product_of_arguments:
        iterations = (
            1000 if args.minimal else number_of_iterations(num_of_concurrent_tasks)
        )
        anyio.run(
            main,
            args.backend,
            iterations,
            num_of_concurrent_tasks,
            data_size,
            host,
            number_of_clients,
            use_tls,
            is_cluster,
            compression_backend,
            compression_level,
            min_compression_size,
            backend=args.backend,
        )

    process_results()
    
    print(f"\nBenchmark completed! Results saved to: {args.resultsFile}")
    print("\nSummary:")
    for result in bench_json_results:
        compression_status = "with compression" if result["compression_enabled"] else "without compression"
        print(f"  {result['client']} ({compression_status}): {result['tps']} TPS, "
              f"avg latency: {result['set_average_latency']:.2f}ms")
