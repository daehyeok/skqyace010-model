## Context

See proposal.md (Why). Current state:

- `build.export(out_dir)` builds `model.parts()` (five solids). It runs `checks.check_parts`, `check_cover` and `check_envelope`, writes the STEP from `model.assembly()` (which carries `model.PART_COLORS`) and the STL from `model.fused()` into a temp dir under `out_dir`, normalises both files, runs `checks.check_outputs`, and then `os.replace`s them into place. It returns `(step, stl)`.
- `tests/test_outputs.py` unpacks `step, stl = build.export(...)` in its fixture and in the rebuild and failure tests.
- `uv.lock` already pins matplotlib 3.11.2, numpy, pillow and vtk 9.6.2, all transitively through `vtk` (a cadquery-ocp dependency). No new package has to be downloaded.
- `tests/test_no_local_refs.py` already skips `.png` files.

## Goals / Non-Goals

**Goals:**
- A coloured, shaded isometric PNG that is generated and checked by `build-model` and committed next to the STEP and STL.
- Headless, cross-platform rendering that is byte-reproducible on one platform.

**Non-Goals:**
- Photorealism (materials, reflections, shadows, anti-aliased edges beyond matplotlib's defaults).
- Multiple views, animations or an SVG version.
- Byte-identical PNGs across different operating systems. Rasterisation and floating-point differences may vary there; the existing reproducibility rule is also per platform.
- Rendering through KiCad.

## Decisions

### 1. Renderer: matplotlib `mplot3d` with the Agg backend

The renderer tessellates each part and draws all the triangles as one `Poly3DCollection` on an Agg canvas.

- *Alternative: VTK offscreen.* VTK is also locked and has a real z-buffer, but offscreen rendering needs an OpenGL context: OSMesa, EGL or a display. The standard `vtk` wheels on headless Linux CI and Windows services often can't create one. That would break the "headless on every supported platform" requirement.
- *Alternative: a custom NumPy z-buffer rasteriser.* It would give exact occlusion, but it's more code to write and maintain than a README picture is worth.
- *Alternative: KiCad `pcb render`.* The user rejected this option; it would also add an external tool to the build.
- matplotlib's Agg backend is pure CPU, already in the lock, and deterministic for a given version.

### 2. Geometry source: in-memory `model.parts()` and `model.PART_COLORS`

The renderer uses the exact solids and colours that `model.assembly()` exports to the STEP, before export. This keeps the PNG equal to the STEP's coloured content.

- *Alternative: re-import the written STEP.* `cq.importers.importStep` returns geometry without the per-part colours, so the colours would have to be matched again by heuristics. It would also add an import pass. The STEP round-trip is already checked separately by `check_outputs`.

### 3. Tessellation and shading

- Each part is tessellated with `Shape.tessellate(tolerance=0.01, angularTolerance=0.1)`, the same deflection as the STL, so the stem stays round.
- Flat Lambert shading is computed in NumPy: `colour × (ambient + diffuse × max(0, n·L))`, with fixed `ambient=0.35`, `diffuse=0.65` and a fixed light direction from the upper front left. The resulting per-face RGB is passed as `facecolors`, and matplotlib's own `shade` stays off, so the result depends only on our constants.
- `edgecolor` is set to the face colour with a thin line width, to hide hairline seams between triangles.

### 4. Camera, framing and canvas

- `figsize=(12, 9)` at `dpi=100` gives exactly 1200 × 900 px. The axes fill the figure (`[0, 0, 1, 1]`) and `axis("off")` is set.
- View: `elev=30`, `azim=-72` (frontal enough that both terminals show; -60 hid the -X terminal behind the body), with `proj_type="ortho"` so the datasheet proportions are kept. `set_box_aspect` is set from the bounding-box extents, so millimetres stay equal on every axis. The limits are the model bounding box plus a small margin; `check_envelope` already guarantees its value.
- Background: opaque `#f2f2f2` on both the figure and the axes panes. It keeps the black base visible in GitHub's light and dark themes.

### 5. Depth ordering

All triangles of all parts go into one `Poly3DCollection` with `computed_zorder=True` (the default), so matplotlib sorts per polygon by depth. One collection per part would sort whole parts against each other, which is wrong where the stem passes through the cover.

The first render showed the predicted artefacts: long sliver triangles from the planar cover and base faces were drawn in the wrong order. Every triangle is therefore bisected across its longest edge until no edge exceeds 0.12 mm (`MAX_EDGE`). That gives about 290 k compact triangles, which sort correctly, and adds about 4 s to the build.

### 6. Determinism

- `matplotlib.use("Agg")` is selected inside the render module before pyplot is imported, and an explicit `Figure()` with `FigureCanvasAgg` is used (no pyplot global state).
- The PNG is saved with `metadata={"Software": None}` to drop matplotlib's version string. Agg writes no timestamp. `pil_kwargs` is not used.
- The render draws no text, so fonts and font caches can't affect the output.
- Triangles are emitted in a fixed order: parts in `model.parts()` order, then faces in tessellation order.

### 7. Build integration and checks

- New module `src/skqyace010/render.py` with `render_png(parts, colors, path, bbox)`.
- `build.export` renders into the same temp dir after the STEP and STL. A new `checks.check_png(path)` uses Pillow (locked) and raises `CheckError` unless:
  - the image is 1200 × 900 RGB(A);
  - at least 15 % of its pixels differ from the background;
  - pixels close to each of the four base colours are present, within the shading range.
- `export` returns `(step, stl, png)`, and all three files are moved into place only after every check passes. `main` prints three paths.
- Output name: `models/SKQYACE010.png`, next to the STEP and STL, so the build stays a single atomic step into one directory.

### 8. Dependency declaration

`"matplotlib>=3.8"` is added to `[project].dependencies`, so the build doesn't depend on `vtk` happening to pull it in. `uv lock` must leave the locked version (3.11.2) unchanged. Pillow and NumPy come with matplotlib.

### 9. README

- Place `![SKQYACE010 tact switch, isometric render](models/SKQYACE010.png)` right after the intro paragraph and before the file table.
- Add a `models/SKQYACE010.png` row to the file table ("Isometric render generated by `build-model`, for this README").
- Mention the PNG in the "How the build behaves" checks list.

## Risks / Trade-offs

- [Painter's-algorithm artefacts: a far triangle can be drawn over a near one where large and small faces interleave, such as cover skirts against terminals] → Use a fine tessellation (small, similar-sized triangles sort well) and a view that avoids grazing angles. Inspect the image by eye in review. If artefacts remain, subdivide the large planar faces before sorting.
- [The PNG differs between Linux, macOS and Windows] → This is accepted and matches the existing per-platform reproducibility rule. The committed PNG comes from whichever platform last ran the build, and tests compare only within one run.
- [A matplotlib upgrade in the lock changes the image bytes] → This is expected. Regenerate and commit the image together with the lock change, as is already done for the STEP and STL.
- [The build gets slower] → Tessellating about five small parts and rasterising 1200 × 900 takes a few seconds, which is acceptable.
- [Binary churn in git: each model change rewrites a PNG of about 100 KB] → This is acceptable for a small repository and keeps the README honest.

## Migration Plan

No migration is needed. After the change is applied, run `uv run build-model` once and commit `models/SKQYACE010.png` with the code and README changes. To roll back, revert the commit; the STEP and STL are untouched by this change.
