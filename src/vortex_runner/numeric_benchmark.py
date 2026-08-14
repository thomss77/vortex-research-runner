from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np

from .event_kernel import first_ge, first_le, summarize_r


def run(count: int, windows: int) -> dict[str, float | int | str]:
    rng = np.random.default_rng(20260814)

    r = rng.normal(loc=0.08, scale=1.1, size=count)
    started = perf_counter()
    metrics = summarize_r(r, risk_fraction=0.009, initial_equity=100_000.0)
    metrics_seconds = perf_counter() - started

    series = rng.normal(size=max(4096, windows * 64)).cumsum()
    starts = np.arange(windows, dtype=np.int64) * 32
    ends = starts + 64

    started = perf_counter()
    checksum = 0
    for start, end in zip(starts, ends, strict=True):
        center = float(series[int(start)])
        checksum += first_ge(series, center + 1.0, int(start), int(end))
        checksum += first_le(series, center - 1.0, int(start), int(end))
    scan_seconds = perf_counter() - started

    return {
        "benchmark": "generic-numeric-kernel-v2",
        "detected_cpu_count": int(os.cpu_count() or 1),
        "r_value_count": int(count),
        "metric_seconds": round(metrics_seconds, 6),
        "metric_values_per_second": round(count / metrics_seconds, 3)
        if metrics_seconds > 0
        else float("inf"),
        "window_count": int(windows),
        "window_scan_seconds": round(scan_seconds, 6),
        "window_scans_per_second": round((2 * windows) / scan_seconds, 3)
        if scan_seconds > 0
        else float("inf"),
        "checksum": int(checksum),
        "final_equity": round(metrics.final_equity, 6),
        "max_drawdown_pct": round(metrics.max_drawdown_pct, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1_000_000)
    parser.add_argument("--windows", type=int, default=20_000)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    if args.count < 1 or args.windows < 1:
        raise SystemExit("count and windows must be >= 1")

    report = run(args.count, args.windows)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json is not None:
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
