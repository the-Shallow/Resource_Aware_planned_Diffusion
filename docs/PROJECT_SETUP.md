# Project setup and repository handoff

## Repository identity

This working tree began from the official Planned Diffusion repository at
commit `5c52637473c1a1f1fe78d87bcc0e407e73881fbc`.

The clone initially names the official repository `origin`. Before adding your
own repository, rename that remote to `upstream`, then use `origin` for the
shared project repository:

```bash
git remote rename origin upstream
git remote -v
git remote add origin git@github.com:<owner>/<repository>.git
git push -u origin main
```

If using HTTPS instead of SSH:

```bash
git remote add origin https://github.com/<owner>/<repository>.git
git push -u origin main
```

Invite the coworker through the hosting service's repository settings. They can
then run:

```bash
git clone git@github.com:<owner>/<repository>.git
cd <repository>
git remote add upstream https://github.com/planned-diffusion/planned-diffusion.git
```

Do not paste access tokens into remote URLs, shell history, configuration files,
or chat messages.

## Licensing note

The inspected upstream snapshot does not contain a `LICENSE` file. Before
making a derived repository public or redistributing upstream source, confirm
the authors' intended license or obtain permission. A private course-project
repository is the cautious default until this is resolved. Do not add a license
that purports to relicense upstream code.

## Local environment

The pinned upstream dependencies target Python 3.10 and CUDA-enabled PyTorch.
Use a dedicated environment:

```bash
conda create -n planned-diffusion python=3.10 -y
conda activate planned-diffusion
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
```

Verify the environment:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"
python -m pytest
```

The official model may require substantial GPU memory and a Hugging Face
download. Keep checkpoints outside Git and authenticate with the Hugging Face
CLI or environment-managed credentials when required.

## Repository layout

```text
dream/                      upstream Dream model and generation code
eval/                       upstream generation and evaluation entry points
train/                      upstream training code
semantic_parallel/          project-owned implementation area
  scheduler/                C++ scheduler, bindings, and Python adapter
  distributed/              coordinator and worker execution
  profiling/                timing, metrics, and experiment records
tests/                      fast CPU/unit tests
docs/                       setup, design, and experiment documentation
CODEBASE_ANALYSIS.md        verified call graph, risks, and phased plan
```

## Upstream synchronization

Inspect changes before merging them; upstream modifications may overlap future
project hooks:

```bash
git fetch upstream
git log --oneline --left-right main...upstream/main
git diff main...upstream/main
```

Do not merge upstream blindly after project work begins. Use a reviewed pull
request or a dedicated integration branch.

## First shared milestone

Both contributors should be able to:

1. clone the project repository;
2. create the Python 3.10 environment;
3. import the package and run CPU unit tests;
4. identify the exact upstream commit;
5. work on separate branches and open reviewed pull requests.

GPU baseline reproduction is the next implementation checkpoint, not part of
this repository-setup step.

## Uploading the working tree to CSC ARC

The PowerShell uploader uses the same CSC ARC account and SSH key convention as
the earlier CSC 548 homework:

```powershell
.\scripts\upload_to_arc.ps1
```

Its defaults are:

```text
account:     kpatel53@arc.csc.ncsu.edu
SSH key:     C:\Users\khush\.ssh\arc_v3
destination: ~/Resource_Aware_planned_Diffusion
```

Override any value when needed:

```powershell
.\scripts\upload_to_arc.ps1 `
    -ArcUser kpatel53 `
    -ArcHost arc.csc.ncsu.edu `
    -IdentityFile C:\Users\khush\.ssh\arc_v3 `
    -RemoteDirectory Resource_Aware_planned_Diffusion
```

The archive includes the source tree and `.git` history. It excludes the local
Windows virtual environment, caches, model weights, logs, and generated results.
Those files are platform-specific or too large and should be created directly
on ARC.
