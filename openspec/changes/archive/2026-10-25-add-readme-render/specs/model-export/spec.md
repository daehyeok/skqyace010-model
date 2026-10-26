## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Single command produces STEP and STL

One command, `uv run build-model`, SHALL regenerate `models/SKQYACE010.step`, `models/SKQYACE010.stl` and the preview image `models/SKQYACE010.png` from the CadQuery source.

#### Scenario: Successful build

- **WHEN** `uv run build-model` runs in a synced environment
- **THEN** it writes all three files, prints their paths and exits 0

#### Scenario: Failed build leaves outputs untouched

- **WHEN** the model raises an error, fails the built-in sanity checks (envelope, solid validity), or the image fails its check
- **THEN** the command exits non-zero and leaves the previously committed STEP, STL and PNG in `models/` unchanged

### Requirement: Reproducible output

Building twice from the same source and lockfile SHALL produce byte-identical STEP, STL and PNG files on the same platform. No wall-clock timestamps or machine-specific values SHALL appear in the outputs, including PNG metadata chunks.

#### Scenario: Rebuild is a no-op

- **WHEN** `uv run build-model` is run on an unchanged checkout whose committed outputs are current
- **THEN** `git status` shows no modification under `models/`

#### Scenario: PNG carries no varying metadata

- **WHEN** the PNG's metadata chunks are listed
- **THEN** none of them holds a timestamp, software version string, host name or file path
