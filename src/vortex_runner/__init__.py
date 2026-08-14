"""Public, strategy-agnostic research runner."""

from .core import BatchConfig, BatchReport, run_batch

__all__ = ["BatchConfig", "BatchReport", "run_batch"]
__version__ = "0.1.0"
