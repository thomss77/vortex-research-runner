from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import islice
import os
from time import perf_counter
from typing import Callable, Iterable, Iterator, Sequence, TypeVar

T = TypeVar("T")
R = TypeVar("R")

_WORKER_EVALUATOR: Callable[[object], object] | None = None


@dataclass(frozen=True)
class BatchConfig:
    workers: int | None = None
    chunk_size: int = 256


@dataclass(frozen=True)
class BatchReport:
    candidate_count: int
    duration_seconds: float
    candidates_per_second: float
    workers: int
    chunk_size: int


def _resolve_workers(requested: int | None) -> int:
    cpu_count = os.cpu_count() or 1
    if requested is None or requested <= 0:
        return max(1, cpu_count)
    return max(1, min(int(requested), cpu_count))


def _chunked(values: Sequence[T], chunk_size: int) -> Iterator[list[T]]:
    for start in range(0, len(values), chunk_size):
        yield list(values[start : start + chunk_size])


def _init_worker(evaluator: Callable[[object], object]) -> None:
    global _WORKER_EVALUATOR
    _WORKER_EVALUATOR = evaluator


def _evaluate_chunk(chunk: list[object]) -> list[object]:
    if _WORKER_EVALUATOR is None:
        raise RuntimeError("worker evaluator was not initialized")
    return [_WORKER_EVALUATOR(candidate) for candidate in chunk]


def run_batch(
    candidates: Iterable[T],
    evaluator: Callable[[T], R],
    config: BatchConfig | None = None,
) -> tuple[list[R], BatchReport]:
    """Evaluate candidates while keeping strategy logic outside this package.

    The evaluator must be a top-level picklable callable when workers > 1.
    Candidate ordering is preserved in the returned result list.
    """

    cfg = config or BatchConfig()
    if cfg.chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")

    materialized = list(candidates)
    workers = _resolve_workers(cfg.workers)
    started = perf_counter()

    if not materialized:
        duration = perf_counter() - started
        return [], BatchReport(0, duration, 0.0, workers, cfg.chunk_size)

    if workers == 1:
        results = [evaluator(candidate) for candidate in materialized]
    else:
        results = []
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(evaluator,),
        ) as pool:
            for partial in pool.map(
                _evaluate_chunk,
                _chunked(materialized, cfg.chunk_size),
                chunksize=1,
            ):
                results.extend(partial)

    duration = perf_counter() - started
    throughput = len(materialized) / duration if duration > 0 else float("inf")
    report = BatchReport(
        candidate_count=len(materialized),
        duration_seconds=duration,
        candidates_per_second=throughput,
        workers=workers,
        chunk_size=cfg.chunk_size,
    )
    return results, report
