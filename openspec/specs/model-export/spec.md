# model-export Specification

## Purpose

Generate the SKQYACE010 STEP and STL reproducibly from the CadQuery source, in a uv-managed Python environment that can be recreated identically on any developer machine.

## Requirements

### Requirement: Reproducible, cross-platform development environment

The repository SHALL contain everything uv needs to recreate the development environment: a project manifest, a committed lockfile pinning every transitive dependency, and a pinned Python version. Running `uv sync` on a fresh clone SHALL create a project-local virtual environment that has all build and test dependencies, on Linux x86_64, macOS (arm64 and x86_64) and Windows x86_64. Setup SHALL NOT depend on the system Python, pip or any globally installed package; only uv itself is required.

#### Scenario: Fresh clone on another machine

- **WHEN** a developer with only uv installed clones the repo and runs `uv sync`
- **THEN** uv installs the pinned Python if it is missing, creates `.venv` from the lockfile and exits 0, and `uv run build-model` then works

#### Scenario: Lockfile is authoritative

- **WHEN** `uv sync --locked` is run
- **THEN** it succeeds without changing `uv.lock`, and fails if the manifest and the lockfile disagree

#### Scenario: Virtual environment is not committed

- **WHEN** the committed tree is inspected
- **THEN** `.venv/` and Python cache directories are absent, because they are git-ignored

### Requirement: Single command produces STEP and STL

One command, `uv run build-model`, SHALL regenerate both `models/SKQYACE010.step` and `models/SKQYACE010.stl` from the CadQuery source.

#### Scenario: Successful build

- **WHEN** `uv run build-model` runs in a synced environment
- **THEN** it writes both files, prints their paths and exits 0

#### Scenario: Failed build leaves outputs untouched

- **WHEN** the model raises an error or fails the built-in sanity checks (envelope, solid validity)
- **THEN** the command exits non-zero and leaves the previously committed files in `models/` unchanged

### Requirement: STEP output loadable by KiCad

The STEP SHALL be a valid ISO 10303-21 file using the AP214 schema, in millimetres. It SHALL contain one valid closed solid per model part, with the part colours attached. KiCad's 3D viewer and `kicad-cli` (which use OpenCASCADE) SHALL load it without errors.

#### Scenario: KiCad loads the STEP

- **WHEN** a PCB containing `cornet_ec:SKQYACE010` that references the new STEP is exported with `kicad-cli pcb export step`, or opened in the 3D viewer
- **THEN** the switch body appears, and there is no error and no "failed to load" warning for the model

#### Scenario: Round-trip validity

- **WHEN** the generated STEP is re-imported with CadQuery
- **THEN** it yields one valid solid per part (`isValid()` is true), and its bounding box matches the `skqyace010-model` envelope

### Requirement: STL output

The STL SHALL be a closed (watertight) mesh of the whole switch, in millimetres and in the coordinate frame defined by the `skqyace010-model` capability. It SHALL be tessellated finely enough that the stem looks round at board zoom: linear deflection ≤ 0.01 mm and angular deflection ≤ 0.1 rad.

#### Scenario: STL is valid and in frame

- **WHEN** the generated STL is loaded and checked
- **THEN** every edge is shared by exactly two triangles, and the bounding box matches the STEP's bounding box to within 0.01 mm on every axis

### Requirement: Reproducible output

Building twice from the same source and lockfile SHALL produce byte-identical STEP and STL files. No wall-clock timestamps or machine-specific values SHALL appear in the outputs.

#### Scenario: Rebuild is a no-op

- **WHEN** `uv run build-model` is run on an unchanged checkout whose committed outputs are current
- **THEN** `git status` shows no modification under `models/`
