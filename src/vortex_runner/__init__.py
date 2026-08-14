"""Public, strategy-agnostic research runner."""

from .core import BatchConfig, BatchReport, run_batch
from .event_kernel import (
    ExitEvent,
    PerformanceMetrics,
    equity_curve,
    first_ge,
    first_le,
    first_true,
    max_drawdown_pct,
    resolve_barrier_event,
    summarize_r,
)

__all__ = [
    "BatchConfig",
    "BatchReport",
    "ExitEvent",
    "PerformanceMetrics",
    "equity_curve",
    "first_ge",
    "first_le",
    "first_true",
    "max_drawdown_pct",
    "resolve_barrier_event",
    "run_batch",
    "summarize_r",
]
__version__ = "0.2.0"
