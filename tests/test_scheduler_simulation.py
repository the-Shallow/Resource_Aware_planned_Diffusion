"""Tests for synthetic scheduler experiments on the local runtime."""

import math

import pytest

from semantic_parallel.profiling.simulation import (
    make_sleep_executor,
    run_scheduler_simulation,
)
from semantic_parallel.scheduler import schedule_lpt, schedule_round_robin
from semantic_parallel.stage import ChunkTask


def make_tasks() -> list[ChunkTask]:
    costs = [120, 80, 35, 20]
    return [
        ChunkTask(
            chunk_id=chunk_id,
            content_length=cost,
            start=0,
            end_exclusive=0,
        )
        for chunk_id, cost in enumerate(costs)
    ]


@pytest.fixture
def native_scheduler():
    return pytest.importorskip(
        "semantic_parallel.scheduler._scheduler_native",
        reason="native scheduler extension has not been built",
    )


@pytest.mark.parametrize("invalid_scale", [-1.0, math.inf, -math.inf, math.nan])
def test_sleep_executor_rejects_invalid_scale(invalid_scale):
    with pytest.raises(ValueError):
        make_sleep_executor(invalid_scale)


def test_sleep_executor_returns_worker_and_chunk_identity():
    execute_task = make_sleep_executor(0.0)

    assert execute_task(make_tasks()[2], worker_id=3) == "result-2-from-3"


@pytest.mark.parametrize(
    ("policy", "worker_count", "expected_loads"),
    [
        (schedule_round_robin, 1, (255.0,)),
        (schedule_round_robin, 2, (155.0, 100.0)),
        (schedule_round_robin, 4, (120.0, 80.0, 35.0, 20.0)),
        (schedule_lpt, 1, (255.0,)),
        (schedule_lpt, 2, (120.0, 135.0)),
        (schedule_lpt, 4, (120.0, 80.0, 35.0, 20.0)),
    ],
)
def test_simulation_runs_policies_with_1_2_and_4_workers(
    native_scheduler,
    policy,
    worker_count,
    expected_loads,
):
    result = run_scheduler_simulation(
        tasks=make_tasks(),
        worker_count=worker_count,
        scheduler_policy=policy,
        seconds_per_cost=0.0,
    )

    assert result.policy_name == policy.__name__
    assert result.worker_count == worker_count
    assert result.sequential_seconds == 0.0
    assert result.measured_speedup == 0.0
    assert tuple(
        worker.predicted_load
        for worker in result.stage_execution.worker_executions
    ) == expected_loads
    assert tuple(
        int(output.split("-")[1])
        for output in result.stage_execution.ordered_outputs
    ) == (0, 1, 2, 3)

    executed_chunk_ids = sorted(
        execution.chunk_id
        for worker in result.stage_execution.worker_executions
        for execution in worker.task_executions
    )
    assert executed_chunk_ids == [0, 1, 2, 3]


@pytest.mark.parametrize("policy", [schedule_round_robin, schedule_lpt])
def test_parallel_simulation_reports_measured_speedup(
    native_scheduler,
    policy,
):
    result = run_scheduler_simulation(
        tasks=make_tasks(),
        worker_count=2,
        scheduler_policy=policy,
        seconds_per_cost=0.002,
    )

    assert result.sequential_seconds == pytest.approx(0.51)
    assert result.measured_speedup == pytest.approx(
        result.sequential_seconds / result.stage_execution.elapsed_seconds
    )
    assert result.measured_speedup > 1.0
