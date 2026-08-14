# vortex-research-runner

Public, strategy-agnostic engine for high-throughput quantitative research workloads.

This repository contains only reusable infrastructure and generic numerical primitives. It does **not** contain private trading rules, private parameters, champions, symbols, setup selection, proprietary indicator combinations or strategy-specific TP/SL definitions.

## What it does

- Executes large candidate batches with configurable process workers and chunk sizes.
- Preserves candidate/result ordering and reports candidates per second.
- Provides generic NumPy equity, drawdown and R-metric kernels.
- Provides generic first-hit and stop/target/dynamic event resolution.
- Benchmarks both multiprocessing throughput and numerical event kernels on GitHub-hosted runners.
- Can be imported by private research projects as a normal Python dependency.

The event engine is deliberately generic: the consuming private project decides **when to enter, which rules are active, how stop/target levels are constructed, which exit family is chosen, and which candidates exist**. Those strategy decisions are not stored here.

## Local benchmark

```bash
python -m pip install -e . pytest
python -m pytest -q
python -m vortex_runner.benchmark --count 100000 --workers auto --chunk-size 512
python -m vortex_runner.numeric_benchmark --count 1000000 --windows 20000
```

## Public/private boundary

Public:
- batching and multiprocessing;
- generic numerical metrics;
- generic barrier/event scanning;
- synthetic benchmarks and tests.

Private consumer:
- strategy signals and filters;
- indicator grammar and combinations;
- symbol-specific logic;
- setup-specific TP/SL/BE/exit construction;
- candidate generation, champion evolution and research results.

No license has been granted for this repository at this time. See `NOTICE`.
