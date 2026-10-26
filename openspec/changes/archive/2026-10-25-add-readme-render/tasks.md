## 1. Dependency

- [x] 1.1 Add `"matplotlib>=3.8"` to `[project].dependencies` in `pyproject.toml`, then run `uv lock`. Verify that `uv.lock` still pins matplotlib 3.11.2, that `git diff uv.lock` shows only the new manifest entry, and that `uv sync --locked` succeeds.

## 2. Renderer

- [x] 2.1 Create `src/skqyace010/render.py` with `render_png(parts, colors, path, bbox)`. It uses the Agg backend with an explicit `Figure`/`FigureCanvasAgg` and no pyplot. Each part is tessellated at 0.01 mm / 0.1 rad and drawn as one `Poly3DCollection`, with fixed Lambert face colours (ambient 0.35, diffuse 0.65, fixed light vector). The view is orthographic, elev 30 / azim -72 (changed from -60 so both terminals show; see design), with equal box aspect, axes off, an opaque `#f2f2f2` background and a 12 × 9 in canvas at 100 dpi. It saves with `metadata={"Software": None}`. Verify by calling it from a scratch `uv run python -c ...` that writes a 1200 × 900 PNG to a temp path.
- [x] 2.2 Look at the scratch PNG. Check that the stem, cover tier, both terminals and the black base ends are visible, in four distinct colours, with no obvious depth-sorting artefacts. Tune the light vector, margin, edge width or view only if needed (done: longest-edge subdivision to 0.12 mm fixed the depth-sorting artefacts), and record the final constants in the module.

## 3. Build integration and checks

- [x] 3.1 Add `checks.check_png(path)` in `src/skqyace010/checks.py`, using Pillow. It raises `CheckError` unless the image is 1200 × 900, at least 15 % of its pixels differ from the background, and pixels close to each of the four base part colours are present. Verify with a unit test in `tests/test_outputs.py` that feeds it a blank 1200 × 900 image and expects `CheckError`.
- [x] 3.2 Update `build.export` to render `SKQYACE010.png` into the temp dir after the STEP and STL, run `check_png`, and move all three files into place only after every check passes. It returns `(step, stl, png)`. Update `main` to print the three paths and update the module docstring. Verify that `uv run build-model` prints three paths and exits 0.
- [x] 3.3 Update `tests/test_outputs.py` for the 3-tuple. The fixture and `test_build_writes_both_files` assert that exactly the three outputs remain. `test_rebuild_is_byte_identical` also compares the PNG bytes. `test_failed_build_leaves_outputs_untouched` also snapshots the PNG. Add a test that the PNG's metadata chunks hold no `Software`, time, host or path entries. Verify with `uv run pytest tests/test_outputs.py`.
- [x] 3.4 Add a test that runs the render with `DISPLAY` and `WAYLAND_DISPLAY` removed from the environment (via `monkeypatch.delenv`) and confirms the PNG is produced. Verify with `uv run pytest -k headless`.

## 4. Outputs and README

- [x] 4.1 Run `uv run build-model` and commit-stage `models/SKQYACE010.png`. Verify that a second `uv run build-model` leaves `git status` clean under `models/`, and that the STEP and STL bytes are unchanged from before this change.
- [x] 4.2 Edit `README.md`: put `![SKQYACE010 tact switch, isometric render](models/SKQYACE010.png)` after the intro paragraph and before the file table, add a `models/SKQYACE010.png` row to the file table, and mention the image and its check in "How the build behaves". Verify by previewing the Markdown (for example on the repo web page or with a local Markdown viewer) that the image displays above "Provenance".
- [x] 4.3 Add a test in `tests/` that parses the image references in `README.md` and asserts that each one resolves to an existing file produced by `build-model` (currently only `models/SKQYACE010.png`). Verify with `uv run pytest`.

## 5. Final verification

- [x] 5.1 Run the full suite with `uv run pytest`. Everything must pass, and the KiCad test may skip if `kicad-cli` is absent. Run `openspec validate add-readme-render --strict` and confirm that it passes.
