"""CadQuery model of the Alps Alpine SKQYACE010 TACT switch.

Pure geometry: every function returns CadQuery objects and performs no I/O.
All dimensions come from :mod:`skqyace010.dims`.
"""

from __future__ import annotations

import cadquery as cq

from skqyace010 import dims as d

# Colours: close to the KiCad 3D-library conventions; appearance follows
# product photos (reference only, not part of the repository).
BASE_COLOR = cq.Color(0.15, 0.15, 0.15)  # black plastic
COVER_COLOR = cq.Color(0.80, 0.80, 0.82)  # stainless steel
STEM_COLOR = cq.Color(0.40, 0.27, 0.20)  # brown
TERMINAL_COLOR = cq.Color(0.86, 0.74, 0.50)  # gold

PART_NAMES = ("base", "cover", "stem", "terminal1", "terminal2")

_EPS = 0.01  # cutter overshoot, so boolean cuts never leave zero-thickness skins


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> cq.Workplane:
    """Axis-aligned box between the given coordinates."""
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


def _lens(z0: float, z1: float, grow: float = 0.0) -> cq.Workplane:
    """The stem's lens profile (1.8 circle + 2.6 x 1.2 lobes), grown by ``grow``."""
    centre = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .circle(d.STEM_D / 2 + grow)
        .extrude(z1 - z0)
    )
    lobes = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .rect(d.STEM_LOBE_W + 2 * grow, d.STEM_LOBE_H + 2 * grow)
        .extrude(z1 - z0)
        .edges("|Z")
        .fillet(d.STEM_LOBE_R + grow)
    )
    return centre.union(lobes).clean()


def cover() -> cq.Workplane:
    """Stainless sheet-metal cover.

    A top plate ending short of the body's X ends, the pressed raised tier
    (filled) with a lens-shaped opening for the stem, skirts down the +-Y faces
    with a notch at the bottom centre, and latch tabs at the plate corners.
    """
    t = d.COVER_T
    y_out = d.BODY_D / 2
    plate_z0 = d.BODY_H - t
    plate = _box(-d.COVER_X, d.COVER_X, -y_out, y_out, plate_z0, d.BODY_H)
    tier = (
        cq.Workplane("XY")
        .workplane(offset=d.BODY_H)
        .rect(d.TIER_W, d.TIER_D)
        .extrude(d.TIER_TOP - d.BODY_H)
        .edges("|Z")
        .fillet(d.TIER_R)
        .faces(">Z")
        .edges()
        .fillet(d.TIER_EDGE_R)
    )
    shell = plate.union(tier)
    notch = (
        _box(-d.NOTCH_W / 2, d.NOTCH_W / 2, -y_out - _EPS, y_out + _EPS,
             d.SKIRT_BOTTOM - _EPS, d.NOTCH_TOP)
        .edges("|Y and >Z")
        .fillet(d.NOTCH_R)
    )
    for sign in (-1, 1):
        y0, y1 = sorted((sign * (y_out - t), sign * y_out))
        skirt = _box(-d.SKIRT_X, d.SKIRT_X, y0, y1, d.SKIRT_BOTTOM, plate_z0 + _EPS)
        shell = shell.union(skirt)
        for xsign in (-1, 1):
            x0, x1 = sorted((xsign * d.SKIRT_X, xsign * (d.SKIRT_X + d.LATCH_W)))
            latch = _box(x0, x1, y0, y1, d.BODY_H - d.LATCH_H, plate_z0 + _EPS)
            shell = shell.union(latch)
    shell = shell.cut(notch)
    opening = _lens(plate_z0 - _EPS, d.TIER_TOP + _EPS, grow=d.STEM_CLEAR)
    return shell.cut(opening).clean()


def base() -> cq.Workplane:
    """Black plastic base: the 6.1 x 3.7 body minus the cover, with end slots.

    It fills everything inside the cover, so it shows at the X ends, through
    the skirt notches, in the ring around the stem and on the underside.
    """
    body = (
        cq.Workplane("XY")
        .box(d.BODY_W, d.BODY_D, d.BODY_H, centered=(True, True, False))
        .edges("|Z")
        .chamfer(d.BODY_CHAMFER)
    )
    body = body.cut(cover())
    slot_top = d.TERMINAL_LEAF_H + 0.1
    for sign in (-1, 1):
        x0, x1 = sorted((sign * d.TERMINAL_FOOT_X, sign * (d.BODY_W / 2 + _EPS)))
        slot = _box(x0, x1, -d.END_SLOT_W / 2, d.END_SLOT_W / 2, -_EPS, slot_top)
        body = body.cut(slot)
    return body.clean()


def stem() -> cq.Workplane:
    """Lens-shaped stem from the base top (inside the tier opening) to Z = 2.5."""
    return _lens(d.BODY_H, d.HEIGHT)


def terminal(side: int) -> cq.Workplane:
    """One terminal: a flat foot on Z = 0 and a leaf slanting up and out.

    Args:
        side: -1 for terminal 1 (pad 1, -X) or +1 for terminal 2 (pad 2, +X).
    """
    if side not in (-1, 1):
        raise ValueError(f"side must be -1 or +1, got {side}")
    t = d.TERMINAL_T
    tip = d.TERMINAL_TIP_X
    base = d.TERMINAL_LEAF_BASE_X
    # Profile of the +X terminal in the XZ plane (x, z), counter-clockwise.
    profile = [
        (d.TERMINAL_FOOT_X, 0.0),
        (tip - t, 0.0),
        (tip, d.TERMINAL_LEAF_H),
        (tip - t, d.TERMINAL_LEAF_H),
        (base, t),
        (d.TERMINAL_FOOT_X, t),
    ]
    # Workplane "XZ" has its normal along -Y, so a symmetric extrude centres
    # the 0.8 width on Y = 0.
    solid = (
        cq.Workplane("XZ")
        .polyline(profile)
        .close()
        .extrude(d.TERMINAL_W / 2, both=True)
    )
    if side < 0:
        solid = solid.mirror("YZ")
    return solid


def parts() -> dict[str, cq.Workplane]:
    """All parts by name (in ``PART_NAMES`` order), in the KiCad frame."""
    return {
        "base": base(),
        "cover": cover(),
        "stem": stem(),
        "terminal1": terminal(-1),
        "terminal2": terminal(+1),
    }


PART_COLORS = {
    "base": BASE_COLOR,
    "cover": COVER_COLOR,
    "stem": STEM_COLOR,
    "terminal1": TERMINAL_COLOR,
    "terminal2": TERMINAL_COLOR,
}


def assembly() -> cq.Assembly:
    """Coloured assembly, one child per part, for STEP export."""
    assy = cq.Assembly(name="SKQYACE010")
    for name, part in parts().items():
        assy.add(part, name=name, color=PART_COLORS[name])
    return assy


def fused() -> cq.Workplane:
    """Every part fused into one solid, for the STL."""
    p = parts()
    result = p[PART_NAMES[0]]
    for name in PART_NAMES[1:]:
        result = result.union(p[name])
    return result.clean()
