"""CPU tests for the reusable local static-stage runtime."""

from threading import Barrier
from time import sleep

import pytest

from semantic_parallel.distributed.local_runtime import run_local_static_stage
from semantic_parallel.scheduler import WorkerAssignment
from semantic_parallel.stage import ChunkTask


def make_task(chunk_id: int, content_length: int = 10) -> ChunkTask:
    return ChunkTask(
        chunk_id=chunk_id,
        content_length=content_length,
        start=0,
        end_exclusive=0,
    )


def make_assignment(
    worker_id: int,
    chunk_ids: tuple[int, ...],
    estimated_load: float,
) -> WorkerAssignment:
    return WorkerAssignment(
        worker_id=worker_id,
        chunk_ids=chunk_ids,
        estimated_load=estimated_load,
    )


def test_local_runtime_starts_workers_concurrently():
    worker_barrier = Barrier(2)

    def execute_task(task, worker_id):
        worker_barrier.wait(timeout=5)
        return f"worker-{worker_id}-chunk-{task.chunk_id}"

    result = run_local_static_stage(
        tasks=[make_task(0), make_task(1)],
        assignments=[
            make_assignment(0, (0,), 10.0),
            make_assignment(1, (1,), 10.0),
        ],
        execute_task=execute_task,
    )

    assert result.ordered_outputs == (
        "worker-0-chunk-0",
        "worker-1-chunk-1",
    )


def test_local_runtime_preserves_worker_order_and_reconstructs_chunk_order():
    tasks = [make_task(0, 20), make_task(1, 50), make_task(2, 30)]
    assignments = [
        make_assignment(1, (1,), 50.0),
        make_assignment(0, (2, 0), 50.0),
    ]

    def execute_task(task, worker_id):
        sleep(0.001)
        return f"result-{task.chunk_id}-from-{worker_id}"

    result = run_local_static_stage(tasks, assignments, execute_task)

    assert tuple(
        worker.worker_id for worker in result.worker_executions
    ) == (0, 1)
    assert result.worker_executions[0].assigned_chunk_ids == (2, 0)
    assert tuple(
        execution.chunk_id
        for execution in result.worker_executions[0].task_executions
    ) == (2, 0)
    assert result.ordered_outputs == (
        "result-0-from-0",
        "result-1-from-1",
        "result-2-from-0",
    )


def test_local_runtime_reports_worker_and_stage_metrics():
    result = run_local_static_stage(
        tasks=[make_task(0)],
        assignments=[make_assignment(0, (0,), 10.0)],
        execute_task=lambda task, worker_id: "done",
    )

    worker = result.worker_executions[0]

    assert result.elapsed_seconds >= worker.compute_seconds >= 0.0
    assert worker.idle_seconds == pytest.approx(
        result.elapsed_seconds - worker.compute_seconds
    )
    assert worker.predicted_load == 10.0
    assert worker.task_executions[0].elapsed_seconds >= 0.0


def test_local_runtime_supports_an_empty_stage():
    result = run_local_static_stage(
        tasks=[],
        assignments=[
            make_assignment(0, (), 0.0),
            make_assignment(1, (), 0.0),
        ],
        execute_task=lambda task, worker_id: "unused",
    )

    assert result.ordered_outputs == ()
    assert len(result.worker_executions) == 2
    assert all(
        worker.task_executions == ()
        for worker in result.worker_executions
    )


def test_local_runtime_propagates_executor_failure():
    def failing_executor(task, worker_id):
        raise RuntimeError(f"worker {worker_id} failed")

    with pytest.raises(RuntimeError, match="worker 0 failed"):
        run_local_static_stage(
            tasks=[make_task(0)],
            assignments=[make_assignment(0, (0,), 10.0)],
            execute_task=failing_executor,
        )
