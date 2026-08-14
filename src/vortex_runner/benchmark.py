from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

from .core import BatchConfig, run_batch


def synthetic_candidate_score(candidate: int) -> float:
    """Deterministic CPU workload used only to benchmark the public engine."""
    x = float(candidate + 1)
    acc = 0.0
    for step in range(24):
        x = math.sin(x * 0.00031 + step) + math.cos(x * 0.00017 - step)
        acc += x * x + math.sqrt(abs(x) + 1.0)
    return acc


def _parse_workers(value: str) -> int | None:
    if value.lower() == "auto":
        return None
    workers = int(value)
    if workers < 1:
        raise argparse.ArgumentTypeError("workers must be >= 1 or 'auto'")
    return workers


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the generic public batch engine")
    parser.add_argument("--count", type=int, default=50_000)
    parser.add_argument("--workers", type=_parse_workers, default=None)
    parser.add_argument("--chunk-size", type=int, default=256)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()

    if args.count < 1:
        raise SystemExit("--count must be >= 1")

    results, report = run_batch(
        range(args.count),
        synthetic_candidate_score,
        BatchConfig(workers=args.workers, chunk_size=args.chunk_size),
    )

    checksum = float(sum(results))
    payload = {
        "engine": "vortex-research-runner",
        "benchmark": "synthetic-cpu-v1",
        "candidate_count": report.candidate_count,
        "duration_seconds": round(report.duration_seconds, 6),
        "candidates_per_second": round(report.candidates_per_second, 3),
        "workers": report.workers,
        "detected_cpu_count": os.cpu_count() or 1,
        "chunk_size": report.chunk_size,
        "checksum": round(checksum, 6),
    }

    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    if args.json_path:
        args.json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
