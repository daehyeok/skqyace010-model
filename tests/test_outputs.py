"""Checks on the generated STEP/STL/PNG files (spec: model-export)."""

import cadquery as cq
import pytest
from PIL import Image

from skqyace010 import build
from skqyace010 import checks
from skqyace010 import dims
from skqyace010 import model
from skqyace010 import render

OUTPUT_NAMES = ["SKQYACE010.png", "SKQYACE010.step", "SKQYACE010.stl"]
PART_RGB = sorted({c.toTuple()[:3] for c in model.PART_COLORS.values()})


@pytest.fixture(scope="module")
def outputs(tmp_path_factory):
    out = tmp_path_factory.mktemp("models")
    return build.export(out)


def test_build_writes_all_files(outputs):
    step, stl, png = outputs
    assert step.name == "SKQYACE010.step" and step.stat().st_size > 0
    assert stl.name == "SKQYACE010.stl" and stl.stat().st_size > 0
    assert png.name == "SKQYACE010.png" and png.stat().st_size > 0
    # Only the three outputs remain; the temporary build dir is cleaned up.
    assert sorted(p.name for p in step.parent.iterdir()) == OUTPUT_NAMES


def test_step_is_ap214_in_mm(outputs):
    text = outputs[0].read_text()
    assert text.startswith("ISO-10303-21;")
    assert "AUTOMOTIVE_DESIGN" in text
    assert "SI_UNIT(.MILLI.,.METRE.)" in text
    assert "2026-01-01T00:00:00" in text


def test_step_round_trip(outputs):
    solids = checks.step_solids(outputs[0])
    assert len(solids) == len(model.PART_NAMES)
    assert all(s.isValid() for s in solids)

    bb = checks.BBox.of_shape(cq.Compound.makeCompound(solids))
    checks.check_envelope(bb, "STEP")


def test_step_has_part_colours_and_true_cylinders(outputs):
    text = outputs[0].read_text()
    assert text.count("STYLED_ITEM(") == len(model.PART_NAMES)
    assert text.count("COLOUR_RGB(") == 4  # base, cover, stem, terminals
    assert "CYLINDRICAL_SURFACE" in text
    for name in model.PART_NAMES:
        assert f"PRODUCT('{name}'" in text


def test_stl_watertight_and_matches_step(outputs):
    step, stl, _ = outputs
    tris = checks.read_stl(stl)
    checks.check_stl_watertight(tris)
    stl_bb = checks.stl_bbox(tris)

    step_bb = checks.BBox.of_shape(cq.Compound.makeCompound(checks.step_solids(step)))
    assert step_bb.max_delta(stl_bb) <= checks.OUTPUT_BBOX_TOL


def test_rebuild_is_byte_identical(outputs, tmp_path):
    step2, stl2, png2 = build.export(tmp_path)
    assert step2.read_bytes() == outputs[0].read_bytes()
    assert stl2.read_bytes() == outputs[1].read_bytes()
    assert png2.read_bytes() == outputs[2].read_bytes()


def test_failed_build_leaves_outputs_untouched(outputs, monkeypatch, capsys):
    before = tuple(p.read_bytes() for p in outputs)
    step = outputs[0]
    monkeypatch.setattr(dims, "TIER_TOP", dims.HEIGHT + 0.1)
    rc = build.main(["--out-dir", str(step.parent)])
    assert rc == 1
    assert "FAILED" in capsys.readouterr().err
    assert tuple(p.read_bytes() for p in outputs) == before
    assert sorted(p.name for p in step.parent.iterdir()) == OUTPUT_NAMES


def test_png_is_a_valid_render(outputs):
    png = outputs[2]
    with Image.open(png) as im:
        assert im.format == "PNG"
        assert im.size == (1200, 900)
    checks.check_png(png, PART_RGB, render.BACKGROUND_RGB)


def test_png_has_no_varying_metadata(outputs):
    with Image.open(outputs[2]) as im:
        im.load()
        text = dict(getattr(im, "text", {}))
    for key in text:
        assert key.lower() not in {"software", "creation time", "date", "author", "source"}
    for value in text.values():
        assert "/" not in value and "\\" not in value  # no file paths
    assert b"tIME" not in outputs[2].read_bytes()


def test_png_check_rejects_blank_image(tmp_path):
    blank = tmp_path / "blank.png"
    Image.new("RGB", (1200, 900), render.BACKGROUND_RGB).save(blank)
    with pytest.raises(checks.CheckError, match="blank"):
        checks.check_png(blank, PART_RGB, render.BACKGROUND_RGB)


def test_png_check_rejects_missing_part_colour(outputs, tmp_path):
    # Paint every stem-coloured pixel grey (any shading, with a wider
    # tolerance than the check uses): the brown check must fail.
    import numpy as np

    with Image.open(outputs[2]) as im:
        px = np.asarray(im.convert("RGB")).copy()
    c = np.array(model.STEM_COLOR.toTuple()[:3])
    p = px.reshape(-1, 3) / 255.0
    s = p @ c / (c @ c)
    resid = np.linalg.norm(p - s[:, None] * c[None, :], axis=1)
    brown = ((resid < 0.08) & (s > 0.2) & (s < 1.2)).reshape(px.shape[:2])
    px[brown] = (128, 128, 128)
    edited = tmp_path / "no_stem.png"
    Image.fromarray(px).save(edited)
    with pytest.raises(checks.CheckError, match="part colour"):
        checks.check_png(edited, PART_RGB, render.BACKGROUND_RGB)


def test_png_check_rejects_wrong_size(tmp_path):
    small = tmp_path / "small.png"
    Image.new("RGB", (600, 450), (0, 0, 0)).save(small)
    with pytest.raises(checks.CheckError, match="expected 1200 x 900"):
        checks.check_png(small, PART_RGB, render.BACKGROUND_RGB)


def test_render_is_headless(monkeypatch, tmp_path):
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    parts = model.parts()
    bbox = checks.BBox.of_shape(model.fused().val())
    png = render.render_png(parts, model.PART_COLORS, tmp_path / "headless.png", bbox)
    checks.check_png(png, PART_RGB, render.BACKGROUND_RGB)


def test_watertight_check_rejects_open_mesh():
    tri = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    with pytest.raises(checks.CheckError):
        checks.check_stl_watertight([tri])


def test_envelope_check_rejects_shifted_model():
    good = checks.BBox(-3.4, -1.85, 0.0, 3.4, 1.85, 2.5)
    checks.check_envelope(good, "good")
    shifted = checks.BBox(-3.4, -1.85, 0.2, 3.4, 1.85, 2.7)
    with pytest.raises(checks.CheckError):
        checks.check_envelope(shifted, "shifted")
