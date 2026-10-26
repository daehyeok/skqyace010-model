# SKQYACE010 3D model

An open 3D model (STEP and STL) of the **Alps Alpine SKQYACE010** TACT switch
(SKQY series, 6.1 × 3.7 × 2.5 mm, top push, surface mount), for the KiCad 3D
viewer. It's a low-detail model built with [CadQuery](https://cadquery.readthedocs.io/).
It is a stand-in for the vendor's STEP, which can't be redistributed.

File | Contents
:--- | :---
`models/SKQYACE010.step` | AP214, mm. Five solids in four colours: base (black plastic), cover (stainless steel), stem (brown), terminal1 and terminal2 (gold). True circular and cylindrical surfaces.
`models/SKQYACE010.stl` | One watertight mesh of the whole switch, mm.

## Provenance

- **Source:** the ALPS SKQY catalogue page, *TACT Switch™ SKQY 6.1 × 3.7 mm (Surface Mount Type)*, page 212, "Dimensions" drawing. Its PDF is not in this repository.
- **No vendor 3D data was used.** The ALPS 3D CAD download (STEP) was never opened by any tool in this repository, and no dimension was measured from it.
- **Estimates:** values that the drawing doesn't dimension were measured off the drawing rasterised at 800 dpi. The scale is calibrated on the 6.1 mm body width (107 px/mm) and cross-checked on the 2.5 mm height (+1.6 %). Every number lives in [`src/skqyace010/dims.py`](src/skqyace010/dims.py) and is commented `datasheet` or `estimate`.
- **Ground terminal:** SKQYACE010 has none, so the ground-terminal features marked ※ in the datasheet are not modelled. The geometry is the same for the other force variants (SKQYAAE010, SKQYABE010, SKQYAFE010).
- **Colours and appearance:** product photos (LCSC part C262417) were used only to see what the part looks like: the stainless cover with its pressed tier, the black plastic ends, the brown stem and the gold terminals. The photos are not included in this repository, and no dimension was taken from them. Every size of the cover features (edges, skirts, notch, latch tabs) was measured off the datasheet drawing.

### Dimensions

Feature | mm | Source
:--- | ---: | :---
Body width × depth | 6.1 × 3.7 | datasheet
Terminal tip to tip | 6.8 | datasheet
Terminal width | 0.8 | datasheet
Height, seating plane to stem top | 2.5 | datasheet
Stem centre diameter | 1.8 | datasheet
Stem width across lobes × lobe height | 2.6 × 1.2 | datasheet
Body height | 1.47 | estimate
Body corner chamfer | 0.4 | estimate
Raised tier (W × D, corner radius) | 4.1 × 2.3, r 0.4 | estimate
Raised tier top | 2.07 | estimate
Stem lobe corner radius | 0.3 | estimate
Terminal thickness / leaf top / foot start | 0.2 / 1.0 / 2.7 | estimate
Cover top-plate end (\|x\|) / sheet thickness | 2.75 / 0.10 | estimate
Cover skirt end (\|x\|) / skirt bottom | 2.62 / 0.18 | estimate
Skirt notch width / top | 2.42 / 0.785 | estimate
Latch tab (W × H) | 0.13 × 0.18 | estimate
Base end slot (W × depth) | 1.5 × 0.3 | estimate

## Using it in KiCad

The model is in KiCad's own coordinate frame:

- Origin at the footprint origin, i.e. the midpoint between pad 1 (X = −3) and pad 2 (X = +3).
- +Z up from the board, with the terminals sitting on Z = 0.
- The terminals run along ±X.

Assign it to the footprint with the identity transform:

```
(model "${KIPRJMOD}/path/to/SKQYACE010.step"
  (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
```

This replaces the vendor model, which needs `rotate (-90, 0, 0)` because it was exported Y-up. The footprint pads are 2.0 × 1.0 mm at X = ±3.0, and the terminal feet land inside them.

## Development

Everything is managed by [uv](https://docs.astral.sh/uv/). `pyproject.toml`, `uv.lock` and `.python-version` (Python 3.12) pin the environment, so it can be recreated on Linux, macOS and Windows.

1. Install uv, using one of these:

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh                     # Linux / macOS
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"           # Windows
   brew install uv  |  nix profile install nixpkgs#uv  |  pipx install uv
   ```

2. Then run:

   ```sh
   uv sync                # create .venv from uv.lock (uv fetches Python 3.12 if needed)
   uv run build-model     # regenerate models/SKQYACE010.{step,stl}
   uv run pytest          # geometry, output, determinism (and KiCad, see below)
   ```

How the build behaves:

- `build-model` writes into a temporary directory and checks the result before moving it into `models/`:
  - every solid is valid;
  - the cover features are present (base visible at the ends, skirt notch, stem clear of the cover);
  - the envelope matches the datasheet;
  - the STEP round-trips;
  - the STL is watertight;
  - the STEP and STL bounding boxes agree.
- If any check fails, the build exits 1 and leaves `models/` unchanged.
- The output is byte-identical between runs on the same platform, because the STEP timestamp and OCCT's run-dependent numbering are normalised. Commit the regenerated files whenever the model changes.

**KiCad check:** `tests/test_kicad.py` exports `tests/kicad/skqyace010_fixture.kicad_pcb` with `kicad-cli` and checks that the switch lands on its pads. The test is skipped if `kicad-cli` is not on `PATH`. To point it elsewhere, set `KICAD_CLI`, for example `KICAD_CLI="$HOME/.bin/kicad.AppImage kicad-cli" uv run pytest`.

## License

[MIT](LICENSE). This covers the code and the generated models.
