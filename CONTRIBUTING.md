# Contributing

## Working agreement

- Keep changes small and tied to one checkpoint in `CODEBASE_ANALYSIS.md`.
- Preserve the official single-GPU path as the correctness baseline.
- Put project-owned code under `semantic_parallel/` whenever possible.
- Avoid broad rewrites of `dream/`, `eval/`, and `train/`. If an upstream file
  must change, explain why in the pull request.
- Do not commit model weights, datasets, credentials, generated outputs, or
  cluster logs.
- Include exact reproduction commands and test results in every pull request.

## Branch and review workflow

Create focused branches from the shared default branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c <initials>/<short-topic>
```

Suggested early work split:

- `baseline/...`: Phase 0 CLI and metrics work.
- `stage-model/...`: `PlannedStage` and `ChunkTask` extraction.
- `scheduler/...`: standalone C++ scheduler and bindings.
- `mock-runtime/...`: simulated distributed executor and metrics.
- `docs/...`: experiment protocol, ARC commands, and report material.

Before opening a pull request:

```bash
python -m pytest
python -m compileall -q dream eval train semantic_parallel tests
ruff check semantic_parallel tests
git diff --check
```

If a test requires GPUs or the full Dream-7B checkpoint, mark that clearly and
include the exact ARC/Slurm command and hardware used. Do not report an
unexecuted command as a passing test.

## Pull-request checklist

- State the checkpoint and scope.
- List every changed upstream file separately from project-owned files.
- Report CPU tests and GPU tests separately.
- Record model/checkpoint revision, seed, dtype, cache mode, and GPU model.
- Explain any output or numerical difference from the single-GPU oracle.
- Update documentation when commands, metrics, or assumptions change.

## Commit style

Use short imperative subjects, for example:

```text
Add structured baseline timing
Extract semantic chunk metadata
Implement LPT scheduler policy
```
