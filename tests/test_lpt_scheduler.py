"""Tests for the native static longest-processing-time scheduler."""

import math

import pytest

pytest.importorskip(
    "semantic_parallel.scheduler._scheduler_native",
    reason="native scheduler extension has not been built",
)

from semantic_parallel.scheduler import WorkerAssignment, schedule_lpt
from semantic_parallel.stage import ChunkTask


def make_task(chunk_id: int, cost: float) -> ChunkTask:
    return ChunkTask(
        chunk_id=chunk_id,
        content_length=cost,
        start=0,
        end_exclusive=0,
    )


def test_lpt_assigns_largest_tasks_to_the_least_loaded_worker():
    tasks = [
        make_task(2, 35),
        make_task(0, 120),
        make_task(3, 20),
        make_task(1, 80),
    ]

    assignments = schedule_lpt(tasks, worker_count=2)

    assert assignments == [
        WorkerAssignment(worker_id=0, chunk_ids=(0,), estimated_load=120.0),
        WorkerAssignment(worker_id=1, chunk_ids=(1, 2, 3), estimated_load=135.0),
    ]


def test_lpt_breaks_equal_cost_and_load_ties_deterministically():
    tasks = [
        make_task(3, 10),
        make_task(1, 10),
        make_task(2, 10),
        make_task(0, 10),
    ]

    assignments = schedule_lpt(tasks, worker_count=2)

    assert assignments == [
        WorkerAssignment(worker_id=0, chunk_ids=(0, 2), estimated_load=20.0),
        WorkerAssignment(worker_id=1, chunk_ids=(1, 3), estimated_load=20.0),
    ]


def test_lpt_keeps_idle_workers_when_workers_outnumber_tasks():
    assignments = schedule_lpt(
        [make_task(1, 10), make_task(0, 20)],
        worker_count=4,
    )

    assert assignments == [
        WorkerAssignment(worker_id=0, chunk_ids=(0,), estimated_load=20.0),
        WorkerAssignment(worker_id=1, chunk_ids=(1,), estimated_load=10.0),
        WorkerAssignment(worker_id=2, chunk_ids=(), estimated_load=0.0),
        WorkerAssignment(worker_id=3, chunk_ids=(), estimated_load=0.0),
    ]


def test_lpt_returns_empty_assignment_for_every_worker():
    assignments = schedule_lpt([], worker_count=2)

    assert assignments == [
        WorkerAssignment(worker_id=0, chunk_ids=(), estimated_load=0.0),
        WorkerAssignment(worker_id=1, chunk_ids=(), estimated_load=0.0),
    ]


@pytest.mark.parametrize("worker_count", [0, -1])
def test_lpt_rejects_nonpositive_worker_count(worker_count):
    with pytest.raises(ValueError, match="worker count must be greater than zero"):
        schedule_lpt([make_task(0, 20)], worker_count=worker_count)


@pytest.mark.parametrize("cost", [-1.0, math.inf, -math.inf, math.nan])
def test_lpt_rejects_invalid_cost(cost):
    with pytest.raises(
        ValueError,
        match="estimated cost must be finite and nonnegative",
    ):
        schedule_lpt([make_task(0, cost)], worker_count=1)
