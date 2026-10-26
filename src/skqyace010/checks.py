"""Checks on the generated model and its output files.

Uses only the standard library plus CadQuery, so the build and the tests share
one implementation.
"""

from __future__ import annotations

import collections
import struct
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from skqyace010 import dims as d

ENVELOPE_TOL = 0.05
OUTPUT_BBOX_TOL = 0.01


class CheckError(Exception):
    """Raised when the model or an output file fails a check."""


@dataclass(frozen=True)
class BBox:
    xmin: float
    ymin: float
    zmin: float
    xmax: float
    ymax: float
    zmax: float

    @classmethod
    def of_shape(cls, shape: cq.Shape) -> "BBox":
        bb = shape.BoundingBox()
        return cls(bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)

    def max_delta(self, other: "BBox") -> float:
        return max(
            abs(a - b)
            for a, b in zip(
                (self.xmin, self.ymin, self.zmin, self.xmax, self.ymax, self.zmax),
                (other.xmin, other.ymin, other.zmin, other.xmax, other.ymax, other.zmax),
            )
        )


def check_envelope(bb: BBox, what: str) -> None:
    """Raises CheckError unless ``bb`` matches the datasheet envelope."""
    expected = {
        "xmin": -d.TERMINAL_SPAN / 2,
        "xmax": d.TERMINAL_SPAN / 2,
        "ymin": -d.BODY_D / 2,
        "ymax": d.BODY_D / 2,
        "zmin": 0.0,
        "zmax": d.HEIGHT,
    }
    for key, want in expected.items():
        got = getattr(bb, key)
        if abs(got - want) > ENVELOPE_TOL:
            raise CheckError(
                f"{what}: {key} = {got:.4f}, expected {want} +- {ENVELOPE_TOL}"
            )


def check_parts(parts: dict[str, cq.Workplane]) -> None:
    """Every part is one valid solid; the stem has a true 1.8 cylinder face."""
    for name, part in parts.items():
        solids = part.solids().vals()
        if len(solids) != 1 or not solids[0].isValid():
            raise CheckError(f"part {name!r} is not one valid solid")
    stem_faces = parts["stem"].faces().vals()
    if not any(
        f.geomType() == "CYLINDER"
        and abs(f._geomAdaptor().Cylinder().Radius() - d.STEM_D / 2) < 1e-6
        for f in stem_faces
    ):
        raise CheckError("stem has no cylindrical face of diameter 1.8")


def check_cover(parts: dict[str, cq.Workplane]) -> None:
    """The datasheet-visible cover features are present.

    * The cover ends short of the body on both X ends (base visible there).
    * No cover material in the skirt notch at X = 0 near the seating plane.
    * The stem passes through the cover without touching it.
    """
    cover = parts["cover"].val()
    bb = cover.BoundingBox()
    min_end_gap = 0.2
    if bb.xmax > d.BODY_W / 2 - min_end_gap or bb.xmin < -d.BODY_W / 2 + min_end_gap:
        raise CheckError(
            f"cover spans x [{bb.xmin:.3f}, {bb.xmax:.3f}]: base not visible at the ends"
        )
    y = d.BODY_D / 2
    probe = cq.Solid.makeBox(
        0.2, 2 * y + 0.2, d.NOTCH_TOP - d.SKIRT_BOTTOM - 0.1,
        cq.Vector(-0.1, -y - 0.1, d.SKIRT_BOTTOM + 0.05),
    )
    if cover.intersect(probe).Volume() > 1e-9:
        raise CheckError("cover has material in the skirt notch at X = 0")
    stem = parts["stem"].val()
    if stem.intersect(cover).Volume() > 1e-9:
        raise CheckError("stem intersects the cover")
    if stem.BoundingBox().zmax <= bb.zmax:
        raise CheckError("stem does not rise above the cover")


def read_stl(path: Path) -> list[tuple[tuple[float, float, float], ...]]:
    """Reads a binary or ASCII STL into a list of triangles."""
    data = path.read_bytes()
    if len(data) >= 84:
        (count,) = struct.unpack_from("<I", data, 80)
        if len(data) == 84 + 50 * count:
            tris = []
            for i in range(count):
                v = struct.unpack_from("<12f", data, 84 + 50 * i)
                tris.append((v[3:6], v[6:9], v[9:12]))
            return tris
    tris = []
    verts: list[tuple[float, float, float]] = []
    for line in data.decode("ascii").splitlines():
        parts = line.split()
        if parts and parts[0] == "vertex":
            verts.append(tuple(float(p) for p in parts[1:4]))
            if len(verts) == 3:
                tris.append(tuple(verts))
                verts = []
    return tris


def stl_bbox(tris) -> BBox:
    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    zs = [v[2] for t in tris for v in t]
    return BBox(min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def check_stl_watertight(tris) -> None:
    """Raises CheckError unless every edge is shared by exactly two triangles."""
    if not tris:
        raise CheckError("STL has no triangles")
    edges: collections.Counter = collections.Counter()
    for tri in tris:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges[frozenset((a, b))] += 1
    bad = sum(1 for n in edges.values() if n != 2)
    if bad:
        raise CheckError(f"STL is not watertight: {bad} edges not shared by 2 triangles")


def step_solids(path: Path) -> list[cq.Solid]:
    """Re-imports a STEP file and returns its solids."""
    return cq.importers.importStep(str(path)).solids().vals()


def check_outputs(step_path: Path, stl_path: Path, n_parts: int) -> None:
    """Validates the STEP and STL files against each other and the envelope."""
    solids = step_solids(step_path)
    if len(solids) != n_parts:
        raise CheckError(f"STEP has {len(solids)} solids, expected {n_parts}")
    for i, solid in enumerate(solids):
        if not solid.isValid():
            raise CheckError(f"STEP solid {i} is not valid")
    step_bb = BBox.of_shape(cq.Compound.makeCompound(solids))
    check_envelope(step_bb, "STEP")

    tris = read_stl(stl_path)
    check_stl_watertight(tris)
    stl_bb = stl_bbox(tris)
    check_envelope(stl_bb, "STL")
    delta = step_bb.max_delta(stl_bb)
    if delta > OUTPUT_BBOX_TOL:
        raise CheckError(f"STEP and STL bounding boxes differ by {delta:.4f} mm")
