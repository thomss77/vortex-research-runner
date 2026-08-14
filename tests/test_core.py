from vortex_runner import BatchConfig, run_batch


def square(value: int) -> int:
    return value * value


def test_sequential_batch_preserves_order() -> None:
    results, report = run_batch(range(8), square, BatchConfig(workers=1, chunk_size=3))
    assert results == [0, 1, 4, 9, 16, 25, 36, 49]
    assert report.candidate_count == 8
    assert report.workers == 1
    assert report.candidates_per_second > 0


def test_parallel_batch_preserves_order() -> None:
    results, report = run_batch(range(32), square, BatchConfig(workers=2, chunk_size=5))
    assert results == [value * value for value in range(32)]
    assert report.candidate_count == 32
    assert report.workers >= 1


def test_empty_batch() -> None:
    results, report = run_batch([], square, BatchConfig(workers=1))
    assert results == []
    assert report.candidate_count == 0
    assert report.candidates_per_second == 0.0
