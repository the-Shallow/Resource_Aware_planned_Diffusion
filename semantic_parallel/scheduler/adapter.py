from __future__ import annotations
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_parallel.stage import ChunkTask

@dataclass(frozen=True)
class WorkerAssignment:
    worker_id: int
    chunk_ids: tuple[int, ...]
    estimated_load: float

def schedule_round_robin(
    tasks: Sequence[ChunkTask],
    worker_count: int
):
    try:
        from . import _scheduler_native
    except ImportError as error:
        raise RuntimeError(
            "The native scheduler extension has not been built."
        ) from error

    native_tasks = [
        _scheduler_native.TaskSpec(
            chunk_id=task.chunk_id,
            estimated_cost=float(task.content_length)
        )
        for task in tasks
    ]

    native_assignments = _scheduler_native.schedule_round_robin(
        native_tasks,
        worker_count
    )

    return [
        WorkerAssignment(
            worker_id=assignment.worker_id,
            chunk_ids=tuple(assignment.chunk_ids),
            estimated_load=assignment.estimated_load
        )
        for assignment in native_assignments
    ]