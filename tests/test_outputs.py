"""Checks on the generated STEP/STL files (spec: model-export)."""

import cadquery as cq
import pytest

from skqyace010 import build
from skqyace010 import checks
from skqyace010 import dims
from skqyace010 import model


@pytest.fixture(scope="module")
def outputs(tmp_path_factory):
    out = tmp_path_factory.mktemp("models")
    step, stl = build.export(out)
    return step, stl


def test_build_writes_both_files(outputs):
    step, stl = outputs
    assert step.name == "SKQYACE010.step" and step.stat().st_size > 0
    assert stl.name == "SKQYACE010.stl" and stl.stat().st_size > 0
    # Only the two outputs remain; the temporary build dir is cleaned up.
    assert sorted(p.name for p in step.parent.iterdir()) == [
        "SKQYACE010.step",
        "SKQYACE010.stl",
    ]


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
    step, stl = outputs
    tris = checks.read_stl(stl)
    checks.check_stl_watertight(tris)
    stl_bb = checks.stl_bbox(tris)

    step_bb = checks.BBox.of_shape(cq.Compound.makeCompound(checks.step_solids(step)))
    assert step_bb.max_delta(stl_bb) <= checks.OUTPUT_BBOX_TOL


def test_rebuild_is_byte_identical(outputs, tmp_path):
    step2, stl2 = build.export(tmp_path)
    assert step2.read_bytes() == outputs[0].read_bytes()
    assert stl2.read_bytes() == outputs[1].read_bytes()


def test_failed_build_leaves_outputs_untouched(outputs, monkeypatch, capsys):
    step, stl = outputs
    before = (step.read_bytes(), stl.read_bytes())
    monkeypatch.setattr(dims, "TIER_TOP", dims.HEIGHT + 0.1)
    rc = build.main(["--out-dir", str(step.parent)])
    assert rc == 1
    assert "FAILED" in capsys.readouterr().err
    assert (step.read_bytes(), stl.read_bytes()) == before
    assert sorted(p.name for p in step.parent.iterdir()) == [
        "SKQYACE010.step",
        "SKQYACE010.stl",
    ]


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
