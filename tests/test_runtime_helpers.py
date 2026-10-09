"""CPU tests for shared stage validation and reconstruction helpers."""

import math

import pytest

from semantic_parallel.distributed.runtime import (
    TaskExecution,
    reconstruct_outputs,
    validate_static_assignments,
)
from semantic_parallel.scheduler import WorkerAssignment
from semantic_parallel.stage import ChunkTask


def make_task(chunk_id: int, content_length: float = 10) -> ChunkTask:
    return ChunkTask(
        chunk_id=chunk_id,
        content_length=content_length,
        start=0,
        end_exclusive=0,
    )


def make_assignment(
    worker_id: int,
    chunk_ids: tuple[int, ...],
    estimated_load: float = 0.0,
) -> WorkerAssignment:
    return WorkerAssignment(
        worker_id=worker_id,
        chunk_ids=chunk_ids,
        estimated_load=estimated_load,
    )


def make_execution(chunk_id: int, output: str) -> TaskExecution[str]:
    return TaskExecution(
        chunk_id=chunk_id,
        worker_id=0,
        output=output,
        elapsed_seconds=0.01,
    )


def test_validate_static_assignments_indexes_a_complete_schedule():
    tasks = [make_task(0, 20), make_task(1, 50), make_task(2, 30)]
    assignments = [
        make_assignment(0, (0, 2), 50.0),
        make_assignment(1, (1,), 50.0),
    ]

    tasks_by_id = validate_static_assignments(tasks, assignments)

    assert list(tasks_by_id) == [0, 1, 2]
    assert tasks_by_id[1] is tasks[1]


def test_validate_static_assignments_allows_empty_workers_and_tasks():
    assignments = [
        make_assignment(0, ()),
        make_assignment(1, ()),
    ]

    assert validate_static_assignments([], assignments) == {}


def test_validate_static_assignments_requires_at_least_one_worker():
    with pytest.raises(ValueError):
        validate_static_assignments([], [])


@pytest.mark.parametrize(
    "tasks",
    [
        [make_task(-1)],
        [make_task(0), make_task(0)],
        [make_task(0, -1)],
        [make_task(0, math.inf)],
        [make_task(0, math.nan)],
    ],
)
def test_validate_static_assignments_rejects_invalid_tasks(tasks):
    with pytest.raises(ValueError):
        validate_static_assignments(tasks, [make_assignment(0, ())])


def test_validate_static_assignments_rejects_unknown_chunk():
    with pytest.raises(ValueError):
        validate_static_assignments(
            [make_task(0)],
            [make_assignment(0, (1,))],
        )


def test_validate_static_assignments_rejects_duplicate_assignment():
    with pytest.raises(ValueError):
        validate_static_assignments(
            [make_task(0)],
            [
                make_assignment(0, (0,)),
                make_assignment(1, (0,)),
            ],
        )


def test_validate_static_assignments_rejects_missing_assignment():
    with pytest.raises(ValueError):
        validate_static_assignments(
            [make_task(0), make_task(1)],
            [make_assignment(0, (0,))],
        )


@pytest.mark.parametrize(
    "assignments",
    [
        [make_assignment(-1, ())],
        [make_assignment(0, ()), make_assignment(0, ())],
        [make_assignment(0, ()), make_assignment(2, ())],
        [make_assignment(0, (), -1.0)],
        [make_assignment(0, (), math.inf)],
        [make_assignment(0, (), math.nan)],
    ],
)
def test_validate_static_assignments_rejects_invalid_workers(assignments):
    with pytest.raises(ValueError):
        validate_static_assignments([], assignments)


def test_reconstruct_outputs_orders_results_by_chunk_id():
    executions = [
        make_execution(2, "result-2"),
        make_execution(0, "result-0"),
        make_execution(1, "result-1"),
    ]

    outputs = reconstruct_outputs(executions, [0, 1, 2])

    assert outputs == ("result-0", "result-1", "result-2")


def test_reconstruct_outputs_rejects_duplicate_expected_ids():
    with pytest.raises(ValueError):
        reconstruct_outputs([], [0, 0])


def test_reconstruct_outputs_rejects_unexpected_result():
    with pytest.raises(ValueError):
        reconstruct_outputs([make_execution(1, "result-1")], [0])


def test_reconstruct_outputs_rejects_duplicate_result():
    with pytest.raises(ValueError):
        reconstruct_outputs(
            [
                make_execution(0, "first"),
                make_execution(0, "second"),
            ],
            [0],
        )


def test_reconstruct_outputs_rejects_missing_result():
    with pytest.raises(ValueError):
        reconstruct_outputs([make_execution(0, "result-0")], [0, 1])
