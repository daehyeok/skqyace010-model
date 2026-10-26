"""Geometry checks on the in-memory model (spec: skqyace010-model)."""

import cadquery as cq
import pytest

from skqyace010 import checks
from skqyace010 import dims as d
from skqyace010 import model

TOL = 0.05


@pytest.fixture(scope="module")
def parts():
    return model.parts()


@pytest.fixture(scope="module")
def fused_bb():
    return model.fused().val().BoundingBox()


def test_datasheet_constants():
    assert (d.BODY_W, d.BODY_D, d.TERMINAL_SPAN, d.TERMINAL_W) == (6.1, 3.7, 6.8, 0.8)
    assert (d.HEIGHT, d.STEM_LOBE_W, d.STEM_LOBE_H, d.STEM_D) == (2.5, 2.6, 1.2, 1.8)


def test_every_part_is_one_valid_solid(parts):
    assert set(parts) == set(model.PART_NAMES)
    for name, part in parts.items():
        solids = part.solids().vals()
        assert len(solids) == 1, name
        assert solids[0].isValid(), name


def test_envelope(fused_bb):
    assert fused_bb.xmin == pytest.approx(-d.TERMINAL_SPAN / 2, abs=TOL)
    assert fused_bb.xmax == pytest.approx(d.TERMINAL_SPAN / 2, abs=TOL)
    assert fused_bb.ylen == pytest.approx(d.BODY_D, abs=TOL)
    assert fused_bb.zmin == pytest.approx(0.0, abs=1e-6)
    assert fused_bb.zmax == pytest.approx(d.HEIGHT, abs=TOL)


def test_body_size(parts):
    bb = parts["base"].val().BoundingBox()
    assert bb.xlen == pytest.approx(d.BODY_W, abs=TOL)
    assert bb.ylen == pytest.approx(d.BODY_D, abs=TOL)
    assert bb.zmin == pytest.approx(0.0, abs=1e-6)
    assert bb.zmax == pytest.approx(d.BODY_H, abs=TOL)
    assert (bb.xmin + bb.xmax) / 2 == pytest.approx(0.0, abs=1e-6)
    assert (bb.ymin + bb.ymax) / 2 == pytest.approx(0.0, abs=1e-6)


def test_cover_size(parts):
    bb = parts["cover"].val().BoundingBox()
    # Ends short of the 6.1 body: the base shows at both X ends.
    assert bb.xmax <= d.COVER_X + 0.01 and bb.xmax < d.BODY_W / 2
    assert bb.xmin >= -d.COVER_X - 0.01
    assert bb.ylen == pytest.approx(d.BODY_D, abs=TOL)
    assert bb.zmin == pytest.approx(d.SKIRT_BOTTOM, abs=TOL)
    assert bb.zmax == pytest.approx(d.TIER_TOP, abs=TOL)


def test_cover_features(parts):
    checks.check_cover(parts)


def test_cover_and_base_do_not_overlap(parts):
    overlap = parts["base"].val().intersect(parts["cover"].val()).Volume()
    assert overlap == pytest.approx(0.0, abs=1e-6)


def test_check_cover_rejects_full_length_cover(monkeypatch):
    monkeypatch.setattr(d, "COVER_X", 3.1)
    with pytest.raises(checks.CheckError):
        checks.check_cover(model.parts())


def test_stem(parts):
    s = parts["stem"]
    bb = s.val().BoundingBox()
    assert bb.xlen == pytest.approx(d.STEM_LOBE_W, abs=TOL)
    assert bb.ylen == pytest.approx(d.STEM_D, abs=TOL)
    assert bb.zmax == pytest.approx(d.HEIGHT, abs=TOL)
    assert (bb.xmin + bb.xmax) / 2 == pytest.approx(0.0, abs=1e-6)
    assert (bb.ymin + bb.ymax) / 2 == pytest.approx(0.0, abs=1e-6)
    cylinders = [f for f in s.faces().vals() if f.geomType() == "CYLINDER"]
    radii = {round(f._geomAdaptor().Cylinder().Radius(), 6) for f in cylinders}
    assert d.STEM_D / 2 in radii, radii


@pytest.mark.parametrize("name,sign", [("terminal1", -1), ("terminal2", 1)])
def test_terminal_foot_on_pad(parts, name, sign):
    t = parts[name]
    bb = t.val().BoundingBox()
    assert bb.zmin == pytest.approx(0.0, abs=1e-6)
    assert bb.ylen == pytest.approx(d.TERMINAL_W, abs=TOL)
    # The face lying on Z = 0 (the foot) must sit inside the land.
    bottom = t.faces("<Z").val().BoundingBox()
    pad_lo = d.PAD_X - d.PAD_L / 2
    pad_hi = d.PAD_X + d.PAD_L / 2
    xs = sorted((sign * bottom.xmin, sign * bottom.xmax))
    assert pad_lo <= xs[0] and xs[1] <= pad_hi, xs
    assert max(abs(bottom.ymin), abs(bottom.ymax)) <= d.PAD_W / 2
    # Tip at the datasheet 6.8 / 2 position.
    tip = bb.xmax if sign > 0 else -bb.xmin
    assert tip == pytest.approx(d.TERMINAL_SPAN / 2, abs=TOL)


def test_assembly_has_coloured_children():
    assy = model.assembly()
    names = [child.name for child in assy.children]
    assert names == list(model.PART_NAMES)
    for child in assy.children:
        assert isinstance(child.color, cq.Color), child.name
    # Four distinct colours: base, cover, stem, terminals (shared by both).
    colours = {child.color.toTuple() for child in assy.children}
    assert len(colours) == 4
    assert model.PART_COLORS["terminal1"] is model.PART_COLORS["terminal2"]
