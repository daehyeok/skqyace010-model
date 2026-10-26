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

One command, `uv run build-model`, SHALL regenerate `models/SKQYACE010.step`, `models/SKQYACE010.stl` and the preview image `models/SKQYACE010.png` from the CadQuery source.

#### Scenario: Successful build

- **WHEN** `uv run build-model` runs in a synced environment
- **THEN** it writes all three files, prints their paths and exits 0

#### Scenario: Failed build leaves outputs untouched

- **WHEN** the model raises an error, fails the built-in sanity checks (envelope, solid validity), or the image fails its check
- **THEN** the command exits non-zero and leaves the previously committed STEP, STL and PNG in `models/` unchanged

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

Building twice from the same source and lockfile SHALL produce byte-identical STEP, STL and PNG files on the same platform. No wall-clock timestamps or machine-specific values SHALL appear in the outputs, including PNG metadata chunks.

#### Scenario: Rebuild is a no-op

- **WHEN** `uv run build-model` is run on an unchanged checkout whose committed outputs are current
- **THEN** `git status` shows no modification under `models/`

#### Scenario: PNG carries no varying metadata

- **WHEN** the PNG's metadata chunks are listed
- **THEN** none of them holds a timestamp, software version string, host name or file path

### Requirement: Rendered preview image

The build SHALL produce `models/SKQYACE010.png`, a PNG raster image of the whole switch for the README. The image SHALL:

- show a single isometric view from above, with the stem, the cover tier and both terminals visible;
- draw each part in the colour that part carries in the STEP (base black, cover stainless-steel grey, stem brown, terminals gold), shaded so that faces at different angles are distinguishable;
- use an opaque light background, so the black base stays visible on both light and dark page themes;
- be 1200 × 900 pixels;
- contain no text, axes, grid or other decoration.

It SHALL be rendered from the same solids and colours that are written to the STEP. Rendering SHALL run headless inside the uv environment, with no display server, GPU, KiCad or other external program, on every platform that the development-environment requirement supports.

#### Scenario: Image is produced with the build

- **WHEN** `uv run build-model` runs in a synced environment
- **THEN** `models/SKQYACE010.png` exists, is a valid PNG of 1200 × 900 pixels, and is not blank: a substantial share of its pixels differ from the background colour

#### Scenario: Part colours are visible

- **WHEN** the generated image is inspected
- **THEN** it contains pixels close to each of the four part colours (dark base, grey cover, brown stem, gold terminals), allowing for shading

#### Scenario: Headless machine

- **WHEN** `uv run build-model` runs on a machine with no display (no `DISPLAY` or `WAYLAND_DISPLAY`, no GPU)
- **THEN** the image is still produced and the build exits 0
