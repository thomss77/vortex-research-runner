from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class PerformanceMetrics:
    trade_count: int
    win_count: int
    loss_count: int
    win_rate_pct: float
    average_r: float
    profit_factor: float
    final_equity: float
    max_drawdown_pct: float


@dataclass(frozen=True)
class ExitEvent:
    index: int
    kind: str
    price: float


def _as_float_array(values: Iterable[float] | np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=np.float64)


def equity_curve(
    r_values: Iterable[float] | np.ndarray,
    *,
    risk_fraction: float = 0.01,
    initial_equity: float = 1.0,
) -> np.ndarray:
    """Return compounded equity after each already-resolved R outcome."""
    if risk_fraction < 0:
        raise ValueError("risk_fraction must be >= 0")
    if initial_equity <= 0:
        raise ValueError("initial_equity must be > 0")

    r = _as_float_array(r_values)
    if r.ndim != 1:
        raise ValueError("r_values must be one-dimensional")
    if r.size == 0:
        return np.empty(0, dtype=np.float64)

    factors = 1.0 + risk_fraction * r
    if np.any(factors < 0.0):
        raise ValueError("an R result would make equity negative")
    return initial_equity * np.multiply.accumulate(factors)


def max_drawdown_pct(equity: Iterable[float] | np.ndarray) -> float:
    values = _as_float_array(equity)
    if values.ndim != 1:
        raise ValueError("equity must be one-dimensional")
    if values.size == 0:
        return 0.0
    if np.any(values < 0.0):
        raise ValueError("equity must be non-negative")

    peaks = np.maximum.accumulate(values)
    drawdowns = np.divide(
        values - peaks,
        peaks,
        out=np.zeros_like(values),
        where=peaks > 0.0,
    )
    return float(abs(np.min(drawdowns)) * 100.0)


def summarize_r(
    r_values: Iterable[float] | np.ndarray,
    *,
    risk_fraction: float = 0.01,
    initial_equity: float = 1.0,
) -> PerformanceMetrics:
    r = _as_float_array(r_values)
    if r.ndim != 1:
        raise ValueError("r_values must be one-dimensional")

    wins = r[r > 0.0]
    losses = r[r < 0.0]
    gross_profit = float(wins.sum()) if wins.size else 0.0
    gross_loss = float(-losses.sum()) if losses.size else 0.0
    if gross_loss == 0.0:
        profit_factor = float("inf") if gross_profit > 0.0 else 0.0
    else:
        profit_factor = gross_profit / gross_loss

    eq = equity_curve(r, risk_fraction=risk_fraction, initial_equity=initial_equity)
    final_equity = float(eq[-1]) if eq.size else float(initial_equity)
    return PerformanceMetrics(
        trade_count=int(r.size),
        win_count=int(wins.size),
        loss_count=int(losses.size),
        win_rate_pct=float((wins.size / r.size) * 100.0) if r.size else 0.0,
        average_r=float(r.mean()) if r.size else 0.0,
        profit_factor=float(profit_factor),
        final_equity=final_equity,
        max_drawdown_pct=max_drawdown_pct(eq),
    )


def first_true(mask: np.ndarray, start: int, end: int) -> int:
    """Return the first true index in [start, end), or -1 when absent."""
    values = np.asarray(mask, dtype=bool)
    start_i = max(0, int(start))
    end_i = min(int(end), int(values.size))
    if end_i <= start_i:
        return -1
    hits = np.flatnonzero(values[start_i:end_i])
    return int(start_i + hits[0]) if hits.size else -1


def first_le(values: np.ndarray, level: float, start: int, end: int) -> int:
    data = _as_float_array(values)
    start_i = max(0, int(start))
    end_i = min(int(end), int(data.size))
    if end_i <= start_i:
        return -1
    hits = np.flatnonzero(data[start_i:end_i] <= float(level))
    return int(start_i + hits[0]) if hits.size else -1


def first_ge(values: np.ndarray, level: float, start: int, end: int) -> int:
    data = _as_float_array(values)
    start_i = max(0, int(start))
    end_i = min(int(end), int(data.size))
    if end_i <= start_i:
        return -1
    hits = np.flatnonzero(data[start_i:end_i] >= float(level))
    return int(start_i + hits[0]) if hits.size else -1


def resolve_barrier_event(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    *,
    start: int,
    end: int,
    side: int,
    stop: float,
    target: float,
    dynamic_mask: np.ndarray | None = None,
    stop_before_target: bool = True,
) -> ExitEvent:
    """Resolve the first generic stop/target/dynamic event in [start, end).

    side is +1 for long and -1 for short. Dynamic exits occur at close and
    lose a same-bar tie to a stop or target event.
    """
    hi = _as_float_array(high)
    lo = _as_float_array(low)
    cl = _as_float_array(close)
    if hi.shape != lo.shape or hi.shape != cl.shape or hi.ndim != 1:
        raise ValueError("high, low and close must be aligned 1-D arrays")
    if side not in (1, -1):
        raise ValueError("side must be +1 or -1")

    start_i = max(0, int(start))
    end_i = min(int(end), int(hi.size))
    if end_i <= start_i:
        raise ValueError("trade window must contain at least one bar")

    if side == 1:
        stop_idx = first_le(lo, stop, start_i, end_i)
        target_idx = first_ge(hi, target, start_i, end_i)
    else:
        stop_idx = first_ge(hi, stop, start_i, end_i)
        target_idx = first_le(lo, target, start_i, end_i)

    dynamic_idx = -1
    if dynamic_mask is not None:
        dynamic = np.asarray(dynamic_mask, dtype=bool)
        if dynamic.shape != hi.shape:
            raise ValueError("dynamic_mask must align with price arrays")
        dynamic_idx = first_true(dynamic, start_i, end_i)

    candidates: list[tuple[int, int, str, float]] = []
    if stop_idx >= 0:
        candidates.append((stop_idx, 0 if stop_before_target else 1, "stop", float(stop)))
    if target_idx >= 0:
        candidates.append((target_idx, 1 if stop_before_target else 0, "target", float(target)))
    if dynamic_idx >= 0:
        candidates.append((dynamic_idx, 2, "dynamic", float(cl[dynamic_idx])))

    if not candidates:
        last = end_i - 1
        return ExitEvent(index=last, kind="time", price=float(cl[last]))

    index, _, kind, price = min(candidates, key=lambda row: (row[0], row[1]))
    return ExitEvent(index=int(index), kind=kind, price=float(price))
