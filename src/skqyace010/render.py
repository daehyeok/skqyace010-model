"""Headless isometric PNG render of the coloured model, for the README.

Draws the same solids and colours that go into the STEP. Each part is
tessellated, flat-shaded with a fixed Lambert light, and rasterised with
matplotlib's Agg backend (pure CPU: no display, GPU or OpenGL needed). Every
input that affects the pixels is a constant here, and the PNG is saved without
a ``Software`` chunk, so output is byte-identical between runs on one platform.
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

WIDTH_PX = 1200
HEIGHT_PX = 900
DPI = 100
BACKGROUND = "#f2f2f2"
BACKGROUND_RGB = (0xF2, 0xF2, 0xF2)

TESS_TOLERANCE = 0.01  # mm, same as the STL
TESS_ANGULAR_TOLERANCE = 0.1  # rad

ELEV = 30.0  # degrees
AZIM = -72.0  # degrees; frontal enough that both terminals show
MAX_EDGE = 0.12  # mm, longest triangle edge after subdivision (see _subdivide)
AMBIENT = 0.35
DIFFUSE = 0.65
# Light from the upper front left (KiCad frame: -Y is the front, +Z up).
LIGHT_DIR = np.array([-0.35, -0.55, 1.0]) / np.linalg.norm([-0.35, -0.55, 1.0])
EDGE_WIDTH = 0.3  # points; hides hairline seams between triangles
MARGIN = 0.15  # mm around the bounding box
ZOOM = 1.25  # mplot3d box zoom, so the switch fills the frame


def _subdivide(tris: np.ndarray) -> np.ndarray:
    """Bisects triangles across their longest edge until no edge exceeds MAX_EDGE.

    matplotlib depth-sorts whole polygons (painter's algorithm), so long sliver
    triangles from planar faces are drawn in the wrong order. Small, compact
    triangles sort correctly. Order is deterministic: kept triangles first, then
    the two halves of each split triangle, in input order.
    """
    while True:
        edges = np.stack(
            [
                np.linalg.norm(tris[:, 1] - tris[:, 0], axis=1),
                np.linalg.norm(tris[:, 2] - tris[:, 1], axis=1),
                np.linalg.norm(tris[:, 0] - tris[:, 2], axis=1),
            ],
            axis=1,
        )
        longest = edges.argmax(axis=1)
        split = edges.max(axis=1) > MAX_EDGE
        if not split.any():
            return tris
        keep, todo, k = tris[~split], tris[split], longest[split]
        # Rotate vertices so the longest edge is (v0, v1); v2 is the apex.
        idx = (np.arange(3)[None, :] + k[:, None]) % 3
        rot = np.take_along_axis(todo, idx[:, :, None], axis=1)
        mid = (rot[:, 0] + rot[:, 1]) / 2
        a = np.stack([rot[:, 0], mid, rot[:, 2]], axis=1)
        b = np.stack([mid, rot[:, 1], rot[:, 2]], axis=1)
        halves = np.stack([a, b], axis=1).reshape(-1, 3, 3)
        tris = np.concatenate([keep, halves])


def _triangles(shape: cq.Shape) -> np.ndarray:
    """Tessellates ``shape`` into an (n, 3, 3) array of small triangles."""
    verts, tris = shape.tessellate(TESS_TOLERANCE, TESS_ANGULAR_TOLERANCE)
    pts = np.array([v.toTuple() for v in verts], dtype=float)
    return _subdivide(pts[np.array(tris, dtype=int)])


def _shade(tris: np.ndarray, rgb: tuple[float, float, float]) -> np.ndarray:
    """Per-triangle Lambert RGB for base colour ``rgb``."""
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 0)
    lambert = np.clip(normals @ LIGHT_DIR, 0.0, 1.0)
    intensity = AMBIENT + DIFFUSE * lambert
    return np.clip(np.outer(intensity, rgb), 0.0, 1.0)


def render_png(
    parts: dict[str, cq.Workplane],
    colors: dict[str, cq.Color],
    path: Path,
    bbox,
) -> Path:
    """Renders ``parts`` in ``colors`` to a 1200 x 900 PNG at ``path``.

    Args:
      parts: solids by name, in a fixed order.
      colors: colour of each part, as used for the STEP.
      path: output PNG path.
      bbox: model bounding box (any object with xmin..zmax), for framing.

    Returns:
      ``path``.
    """
    all_tris = []
    all_rgb = []
    for name, part in parts.items():
        tris = _triangles(part.val())
        rgba = colors[name].toTuple()
        all_tris.append(tris)
        all_rgb.append(_shade(tris, rgba[:3]))
    tris = np.concatenate(all_tris)
    rgb = np.concatenate(all_rgb)

    fig = Figure(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI, facecolor=BACKGROUND)
    FigureCanvasAgg(fig)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0), projection="3d", facecolor=BACKGROUND)
    # One collection, so triangles of all parts are depth-sorted together.
    ax.add_collection3d(
        Poly3DCollection(tris, facecolors=rgb, edgecolors=rgb, linewidths=EDGE_WIDTH)
    )
    lo = np.array([bbox.xmin, bbox.ymin, bbox.zmin]) - MARGIN
    hi = np.array([bbox.xmax, bbox.ymax, bbox.zmax]) + MARGIN
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(tuple(hi - lo), zoom=ZOOM)
    ax.set_proj_type("ortho")
    ax.view_init(elev=ELEV, azim=AZIM)
    ax.set_axis_off()

    fig.savefig(path, format="png", dpi=DPI, facecolor=BACKGROUND, metadata={"Software": None})
    return path
