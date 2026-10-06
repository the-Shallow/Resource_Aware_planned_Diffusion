"""Tests for the native static round-robin scheduler."""

import math

import pytest

pytest.importorskip(
    "semantic_parallel.scheduler._scheduler_native",
    reason="native scheduler extension has not been built",
)

from semantic_parallel.scheduler import WorkerAssignment, schedule_round_robin
from semantic_parallel.stage import ChunkTask


def make_task(chunk_id: int, cost: float) -> ChunkTask:
    return ChunkTask(
        chunk_id=chunk_id,
        content_length=cost,
        start=0,
        end_exclusive=0,
    )


def test_round_robin_is_deterministic_and_reports_worker_loads():
    tasks = [
        make_task(3, 20),
        make_task(1, 80),
        make_task(0, 120),
        make_task(2, 35),
    ]

    assignments = schedule_round_robin(tasks, worker_count=2)

    assert assignments == [
        WorkerAssignment(worker_id=0, chunk_ids=(0, 2), estimated_load=155.0),
        WorkerAssignment(worker_id=1, chunk_ids=(1, 3), estimated_load=100.0),
    ]


def test_round_robin_keeps_idle_workers_when_workers_outnumber_tasks():
    assignments = schedule_round_robin(
        [make_task(0, 20), make_task(1, 50)],
        worker_count=4,
    )

    assert assignments == [
        WorkerAssignment(worker_id=0, chunk_ids=(0,), estimated_load=20.0),
        WorkerAssignment(worker_id=1, chunk_ids=(1,), estimated_load=50.0),
        WorkerAssignment(worker_id=2, chunk_ids=(), estimated_load=0.0),
        WorkerAssignment(worker_id=3, chunk_ids=(), estimated_load=0.0),
    ]


def test_round_robin_returns_empty_assignment_for_every_worker():
    assignments = schedule_round_robin([], worker_count=2)

    assert assignments == [
        WorkerAssignment(worker_id=0, chunk_ids=(), estimated_load=0.0),
        WorkerAssignment(worker_id=1, chunk_ids=(), estimated_load=0.0),
    ]


@pytest.mark.parametrize("worker_count", [0, -1])
def test_round_robin_rejects_nonpositive_worker_count(worker_count):
    with pytest.raises(ValueError, match="worker count must be greater than zero"):
        schedule_round_robin([make_task(0, 20)], worker_count=worker_count)


def test_round_robin_rejects_negative_chunk_id():
    with pytest.raises(ValueError, match="chunk id must be nonnegative"):
        schedule_round_robin([make_task(-1, 20)], worker_count=1)


def test_round_robin_rejects_duplicate_chunk_ids():
    tasks = [make_task(0, 20), make_task(0, 50)]

    with pytest.raises(ValueError, match="chunk id values must be unique"):
        schedule_round_robin(tasks, worker_count=1)


@pytest.mark.parametrize("cost", [-1.0, math.inf, -math.inf, math.nan])
def test_round_robin_rejects_invalid_cost(cost):
    with pytest.raises(
        ValueError,
        match="estimated cost must be finite and nonnegative",
    ):
        schedule_round_robin([make_task(0, cost)], worker_count=1)
