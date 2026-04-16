import argparse
from dataclasses import replace
import h5py
import logging
import logging.config
import multiprocessing.pool
import os
import random
import shutil
import sys
from typing import List

# import docker  <-- Disabled for local-first sovereignty
# import psutil  <-- Disabled for local-first sovereignty

from .definitions import (Definition, InstantiationStatus, algorithm_status,
                                     get_definitions, list_algorithms)
from .constants import INDEX_DIR
from .datasets import DATASETS, get_dataset
from .results import build_result_filepath
from .runner import run, run_docker

# Mock psutil for main.py
class MockVirtualMemory:
    available = 8 * 1024**3 # Simula 8GB disponibili

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("annb")

def positive_int(input_str: str) -> int:
    try:
        i = int(input_str)
        if i < 1: raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError(f"{input_str} is not a positive integer")
    return i

def run_worker(cpu: int, mem_limit: int, args: argparse.Namespace, queue: multiprocessing.Queue) -> None:
    while not queue.empty():
        definition = queue.get()
        if args.local:
            run(definition, args.dataset, args.count, args.runs, args.batch)
        else:
            # run_docker disabilitato se docker non è presente
            logger.error("Docker non disponibile. Usa --local.")

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--dataset", metavar="NAME", help="dataset name", default="glove-100-angular", choices=DATASETS.keys())
    parser.add_argument("-k", "--count", default=10, type=positive_int, help="neighbors count")
    parser.add_argument("--definitions", metavar="FOLDER", default="ann_benchmarks/algorithms")
    parser.add_argument("--algorithm", metavar="NAME", help="run specific algo", default=None)
    parser.add_argument("--docker-tag", default=None)
    parser.add_argument("--list-algorithms", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--runs", type=positive_int, default=5)
    parser.add_argument("--timeout", type=int, default=2 * 3600)
    parser.add_argument("--local", action="store_true", help="Run locally")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--max-n-algorithms", type=int, default=-1)
    parser.add_argument("--run-disabled", action="store_true")
    parser.add_argument("--parallelism", type=positive_int, default=1)
    args = parser.parse_args()
    if args.timeout == -1: args.timeout = None
    return args

def filter_already_run_definitions(definitions, dataset, count, batch, force):
    filtered_definitions = []
    for definition in definitions:
        not_yet_run = [q for q in (definition.query_argument_groups or [[]])
                       if force or not os.path.exists(build_result_filepath(dataset, count, definition, q, batch))]
        if not_yet_run:
            definition = replace(definition, query_argument_groups=not_yet_run) if definition.query_argument_groups else definition
            filtered_definitions.append(definition)
    return filtered_definitions

def check_module_import_and_constructor(df: Definition) -> bool:
    status = algorithm_status(df)
    if status == InstantiationStatus.NO_CONSTRUCTOR:
        raise Exception(f"{df.module}.{df.constructor}: no constructor")
    if status == InstantiationStatus.NO_MODULE:
        logging.warning(f"{df.module}: module not found; skipping")
        return False
    return True

def create_workers_and_execute(definitions: List[Definition], args: argparse.Namespace):
    cpu_count = multiprocessing.cpu_count()
    if args.parallelism > cpu_count - 1:
        raise Exception(f"Parallelism too high")
    if args.batch and args.parallelism > 1:
        raise Exception(f"Batch mode needs parallelism 1")
    task_queue = multiprocessing.Queue()
    for definition in definitions: task_queue.put(definition)
    mem_limit = 1024**3 # 1GB limit statico
    try:
        workers = [multiprocessing.Process(target=run_worker, args=(i + 1, mem_limit, args, task_queue)) for i in range(args.parallelism)]
        [w.start() for w in workers]; [w.join() for w in workers]
    finally:
        [w.terminate() for w in workers]

def main():
    args = parse_arguments()
    if args.list_algorithms:
        list_algorithms(args.definitions); sys.exit(0)
    if os.path.exists(INDEX_DIR):
        shutil.rmtree(INDEX_DIR)
    dataset, dimension = get_dataset(args.dataset)
    definitions = get_definitions(dimension=dimension, point_type=dataset.attrs.get("point_type", "float"),
                                  distance_metric=dataset.attrs["distance"], count=args.count, base_dir=args.definitions)
    random.shuffle(definitions)
    definitions = filter_already_run_definitions(definitions, dataset=args.dataset, count=args.count, batch=args.batch, force=args.force)
    if args.algorithm:
        definitions = [d for d in definitions if d.algorithm == args.algorithm]
    if args.local:
        definitions = list(filter(check_module_import_and_constructor, definitions))
    if len(definitions) == 0:
        raise Exception("Nothing to run")
    create_workers_and_execute(definitions, args)

if __name__ == "__main__":
    main()
