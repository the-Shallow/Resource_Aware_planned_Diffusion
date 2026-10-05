# `semantic_parallel`

This directory owns the CSC 548 project additions. Upstream Planned Diffusion
code should remain in `dream/`, `eval/`, and `train/` with minimal changes.

Planned boundaries:

- `scheduler/`: standalone C++ policies, bindings, and a narrow Python adapter;
- `distributed/`: rank coordination, task execution, synchronization, gather,
  and ordered reconstruction;
- `profiling/`: structured timing, memory, utilization, and experiment output.

The packages are intentionally empty at repository-setup time. Implementation
should follow the checkpoints and correctness gates in `CODEBASE_ANALYSIS.md`.
