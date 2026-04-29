from multiprocessing.pool import ThreadPool
from typing import Any, Dict, Optional
import numpy

class BaseANN(object):
    """Base class/interface for Approximate Nearest Neighbors (ANN) algorithms used in benchmarking."""

    def done(self) -> None:
        """Clean up BaseANN once it is finished being used."""
        pass

    def get_memory_usage(self) -> Optional[float]:
        """Returns the current memory usage of this ANN algorithm instance in kilobytes."""
        return 0

    def fit(self, X: numpy.array) -> None:
        """Fits the ANN algorithm to the provided data."""
        pass

    def query(self, q: numpy.array, n: int) -> numpy.array:
        """Performs a query on the algorithm to find the nearest neighbors."""
        return []

    def batch_query(self, X: numpy.array, n: int) -> None:
        """Performs multiple queries at once."""
        pool = ThreadPool()
        self.res = pool.map(lambda q: self.query(q, n), X)

    def get_batch_results(self) -> numpy.array:
        """Retrieves the results of a batch query."""
        return self.res

    def get_additional(self) -> Dict[str, Any]:
        """Returns additional attributes to be stored with the result."""
        return {}

    def __str__(self) -> str:
        return self.name