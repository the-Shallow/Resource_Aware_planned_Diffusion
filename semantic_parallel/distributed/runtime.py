from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from semantic_parallel.scheduler import WorkerAssignment
from semantic_parallel.stage import ChunkTask

OutputT = TypeVar("OutputT")
TaskExecutor = Callable[[ChunkTask, int], OutputT]

@dataclass(frozen=True)
class TaskExecution(Generic[OutputT]):
    chunk_id: int
    worker_id: int
    output: OutputT
    elapsed_seconds: float

@dataclass(frozen=True)
class WorkerExecution(Generic[OutputT]):
    worker_id: int
    assigned_chunk_ids: tuple[int, ...]
    predicted_load: float
    task_executions: tuple[TaskExecution[OutputT], ...]
    compute_seconds: float
    idle_seconds: float

@dataclass(frozen=True)
class StageExecution(Generic[OutputT]):
    worker_executions: tuple[WorkerExecution[OutputT], ...]
    ordered_outputs: tuple[OutputT, ...]
    elapsed_seconds: float

def validate_static_assignments(
        tasks: Sequence[ChunkTask],
        assignments: Sequence[WorkerAssignment]
):
    if not assignments:
        raise ValueError("at least one worker assignment is required")

    tasks_by_id = {}
    for task in tasks:
        if task.chunk_id < 0:
            raise ValueError("chunk id must be non negative")

        if task.chunk_id in tasks_by_id:
            raise ValueError("task chunk ids must be unique")

        if(not math.isfinite(float(task.content_length)) or task.content_length < 0):
            raise ValueError("task content length must be finite and nonnegative")

        tasks_by_id[task.chunk_id] = task

    worker_ids = set()
    assignment_chunk_ids = set()

    for assignment in assignments:
        if assignment.worker_id < 0:
            raise ValueError("worker id must be nonnegative")

        if assignment.worker_id in worker_ids:
            raise ValueError("worker ids must be unique")

        if(not math.isfinite(assignment.estimated_load) or assignment.estimated_load < 0):
            raise ValueError("estimated load must be finite and non negative")

        worker_ids.add(assignment.worker_id)

        for chunk_id in assignment.chunk_ids:
            if chunk_id not in tasks_by_id:
                raise ValueError("assignment contains unknown chunk id")

            if chunk_id in assignment_chunk_ids:
                raise ValueError("chunk id is assigned more than once")

            assignment_chunk_ids.add(chunk_id)

    expected_worker_ids = set(range(len(assignments)))

    if worker_ids != expected_worker_ids:
        raise ValueError("worker ids must be contigous and start at zero")

    missing_chunk_ids = set(tasks_by_id) - assignment_chunk_ids

    if missing_chunk_ids:
        raise ValueError("task were not assigned")

    return tasks_by_id

def reconstruct_outputs(
        task_executions: Sequence[TaskExecution[OutputT]],
        expected_chunk_ids: Sequence[int]
):
    expected_ids = set(expected_chunk_ids)
    if len(expected_ids) < len(expected_chunk_ids):
        raise ValueError("expected chunk ids must be unique")

    executions_by_id = {}

    for execution in task_executions:
        if execution.chunk_id not in expected_ids:
            raise ValueError("received unexpected chunk id")

        if execution.chunk_id in executions_by_id:
            raise ValueError("received duplicate result for chunk")

        executions_by_id[execution.chunk_id] = execution

    missing_chunk_ids = expected_ids - set(executions_by_id)

    if missing_chunk_ids:
        raise ValueError("missing chunk ids")

    return tuple(executions_by_id[chunk_id].output
                 for chunk_id in sorted(expected_ids)
            )