from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

from semantic_parallel.scheduler import WorkerAssignment
from semantic_parallel.stage import ChunkTask

from .runtime import (
    StageExecution,
    TaskExecution,
    TaskExecutor,
    WorkerExecution,
    reconstruct_outputs,
    validate_static_assignments
)

def _execute_worker(
        assignment: WorkerAssignment,
        tasks_by_id: dict[int, ChunkTask],
        execute_task: TaskExecutor
):
    task_executions = []
    compute_seconds = 0.0

    for chunk_id in assignment.chunk_ids:
        task = tasks_by_id[chunk_id]

        task_start = perf_counter()
        output = execute_task(task, assignment.worker_id)
        task_elapsed = perf_counter() - task_start

        task_executions.append(
            TaskExecution(
                chunk_id=chunk_id,
                worker_id=assignment.worker_id,
                output=output,
                elapsed_seconds=task_elapsed
            )
        )
        compute_seconds += task_elapsed

    return tuple(task_executions), compute_seconds


def run_local_static_stage(tasks, assignments, execute_task):
    tasks_by_id = validate_static_assignments(tasks, assignments)

    ordered_assignments = sorted(
        assignments,
        key= lambda assignment: assignment.worker_id,
    )

    stage_start = perf_counter()

    with ThreadPoolExecutor(max_workers=len(ordered_assignments)) as thread_pool:
        futures = [
            thread_pool.submit(
                _execute_worker,
                assignment,
                tasks_by_id,
                execute_task
            )
            for assignment in ordered_assignments
        ]

        worker_results = [
            future.result()
            for future in futures
        ]

        stage_elapsed = perf_counter() - stage_start

        worker_executions = []

        for assignment, result in zip(ordered_assignments, worker_results):
            task_executions, compute_seconds = result

            worker_executions.append(
                WorkerExecution(
                    worker_id= assignment.worker_id,
                    assigned_chunk_ids= assignment.chunk_ids,
                    predicted_load=assignment.estimated_load,
                    task_executions=task_executions,
                    compute_seconds=compute_seconds,
                    idle_seconds=max(0.0, stage_elapsed - compute_seconds)
                )
            )

        all_task_executions = [
            task_execution
            for worker in worker_executions
            for task_execution in worker.task_executions
        ]

        ordered_outputs = reconstruct_outputs(all_task_executions, list(tasks_by_id))

        return StageExecution(
            worker_executions=tuple(worker_executions),
            ordered_outputs=ordered_outputs,
            elapsed_seconds=stage_elapsed
        )