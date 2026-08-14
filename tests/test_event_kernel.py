import math

import numpy as np

from vortex_runner.event_kernel import (
    equity_curve,
    first_ge,
    first_le,
    first_true,
    max_drawdown_pct,
    resolve_barrier_event,
    summarize_r,
)


def test_vector_metrics():
    r = np.array([1.0, -1.0, 2.0, -0.5])
    eq = equity_curve(r, risk_fraction=0.01, initial_equity=100.0)
    assert eq.shape == (4,)
    assert eq[-1] > 100.0
    assert max_drawdown_pct(eq) > 0.0

    metrics = summarize_r(r, risk_fraction=0.01, initial_equity=100.0)
    assert metrics.trade_count == 4
    assert metrics.win_count == 2
    assert metrics.loss_count == 2
    assert metrics.win_rate_pct == 50.0
    assert math.isclose(metrics.profit_factor, 2.0, rel_tol=1e-12)


def test_first_hit_helpers():
    values = np.array([5.0, 4.0, 3.0, 6.0])
    mask = np.array([False, False, True, True])
    assert first_true(mask, 0, 4) == 2
    assert first_true(mask, 0, 2) == -1
    assert first_le(values, 3.0, 0, 4) == 2
    assert first_ge(values, 6.0, 0, 4) == 3


def test_long_stop_wins_same_bar_tie():
    high = np.array([100.0, 111.0])
    low = np.array([100.0, 89.0])
    close = np.array([100.0, 105.0])
    event = resolve_barrier_event(
        high,
        low,
        close,
        start=1,
        end=2,
        side=1,
        stop=90.0,
        target=110.0,
        stop_before_target=True,
    )
    assert event.index == 1
    assert event.kind == "stop"
    assert event.price == 90.0


def test_short_target_dynamic_and_time_fallbacks():
    high = np.array([100.0, 101.0, 100.0, 99.0])
    low = np.array([100.0, 97.0, 94.0, 96.0])
    close = np.array([100.0, 98.0, 95.0, 97.0])
    dynamic = np.array([False, True, False, False])

    target = resolve_barrier_event(
        high,
        low,
        close,
        start=1,
        end=4,
        side=-1,
        stop=105.0,
        target=95.0,
    )
    assert target.kind == "target"
    assert target.index == 2

    dynamic_exit = resolve_barrier_event(
        high,
        low,
        close,
        start=1,
        end=4,
        side=-1,
        stop=110.0,
        target=90.0,
        dynamic_mask=dynamic,
    )
    assert dynamic_exit.kind == "dynamic"
    assert dynamic_exit.index == 1
    assert dynamic_exit.price == 98.0

    timed = resolve_barrier_event(
        high,
        low,
        close,
        start=1,
        end=4,
        side=1,
        stop=80.0,
        target=120.0,
    )
    assert timed.kind == "time"
    assert timed.index == 3
    assert timed.price == 97.0
