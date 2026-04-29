import argparse
import json
import logging
import os
import threading
import time
from typing import Dict, Optional, Tuple, List, Union

# import colors  <-- Disabled
# import docker  <-- Disabled
import numpy
# import psutil  <-- Disabled

from ann_benchmarks.algorithms.base.module import BaseANN

from .definitions import Definition, instantiate_algorithm
from .datasets import DATASETS, get_dataset
from .distance import dataset_transform, metrics
from .results import store_results

def run_individual_query(algo: BaseANN, X_train: numpy.array, X_test: numpy.array, distance: str, count: int, 
                         run_count: int, batch: bool) -> Tuple[dict, list]:
    prepared_queries = (batch and hasattr(algo, "prepare_batch_query")) or (
        (not batch) and hasattr(algo, "prepare_query")
    )
    best_search_time = float("inf")
    for i in range(run_count):
        print("Run %d/%d..." % (i + 1, run_count))
        n_items_processed = [0]
        def single_query(v: numpy.array) -> Tuple[float, List[Tuple[int, float]]]:
            if prepared_queries:
                algo.prepare_query(v, count)
                start = time.time()
                algo.run_prepared_query()
                total = time.time() - start
                candidates = algo.get_prepared_query_results()
            else:
                start = time.time()
                candidates = algo.query(v, count)
                total = time.time() - start
            
            # Sanitization of results for benchmark distance calculation
            candidates = [(int(idx), float(metrics[distance].distance(v, X_train[idx]))) for idx in candidates]
            n_items_processed[0] += 1
            if n_items_processed[0] % 1000 == 0:
                print("Processed %d/%d queries..." % (n_items_processed[0], len(X_test)))
            return (total, candidates)

        if batch:
            results = [single_query(x) for x in X_test]
        else:
            results = [single_query(x) for x in X_test]
        total_time = sum(time for time, _ in results)
        best_search_time = min(best_search_time, total_time / len(X_test))

    attrs = {
        "batch_mode": batch,
        "best_search_time": best_search_time,
        "name": str(algo),
        "run_count": run_count,
        "distance": distance,
        "count": int(count),
    }
    return (attrs, results)

def load_and_transform_dataset(dataset_name: str):
    D, dimension = get_dataset(dataset_name)
    X_train = numpy.array(D["train"])
    X_test = numpy.array(D["test"])
    distance = D.attrs["distance"]
    return X_train, X_test, distance

def build_index(algo: BaseANN, X_train: numpy.ndarray) -> Tuple:
    t0 = time.time()
    algo.fit(X_train)
    build_time = time.time() - t0
    return build_time, 0 # Index size mock

def run(definition: Definition, dataset_name: str, count: int, run_count: int, batch: bool) -> None:
    algo = instantiate_algorithm(definition)
    X_train, X_test, distance = load_and_transform_dataset(dataset_name)
    try:
        build_time, index_size = build_index(algo, X_train)
        query_argument_groups = [[]]
        if definition.query_argument_groups:
            query_argument_groups = definition.query_argument_groups

        for pos, query_arguments in enumerate(query_argument_groups, 1):
            if hasattr(algo, "set_query_arguments") and query_arguments:
                algo.set_query_arguments(*query_arguments)
            descriptor, results = run_individual_query(algo, X_train, X_test, distance, count, run_count, batch)
            descriptor.update({"build_time": build_time, "index_size": index_size, "algo": definition.algorithm, "dataset": dataset_name})
            store_results(dataset_name, count, definition, query_arguments, descriptor, results, batch)
    finally:
        algo.done()

def run_docker(*args, **kwargs):
    print("Docker disabilitato per questo benchmark locale.")
