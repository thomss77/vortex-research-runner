# vortex-research-runner

Public, strategy-agnostic engine for high-throughput quantitative research workloads.

This repository contains only reusable infrastructure: batch scheduling, CPU multiprocessing, throughput measurement, deterministic benchmarking and tests. It does **not** contain private trading rules, private parameters, champions, symbols, TP/SL logic or proprietary strategy code.

## What it does

- Executes large candidate batches with configurable process workers and chunk sizes.
- Preserves candidate/result ordering.
- Reports elapsed time and candidates per second.
- Includes a deterministic synthetic CPU benchmark so runner performance can be compared over time.
- Can be imported by private research projects as a normal Python dependency.

## Local benchmark

```bash
python -m pip install -e . pytest
python -m pytest -q
python -m vortex_runner.benchmark --count 100000 --workers auto --chunk-size 512
```

## Separation of concerns

The public engine accepts an external evaluator callable. Strategy-specific evaluation remains in the consuming project. This keeps the runner generic and reusable while allowing private projects to retain their own logic and data.

No license has been granted for this repository at this time.
