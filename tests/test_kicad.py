"""KiCad load check (spec: model-export, "KiCad loads the STEP").

Exports the fixture board in ``tests/kicad/`` with ``kicad-cli`` and checks
that the switch arrives on its pads. Skipped when ``kicad-cli`` is not found.
Point ``KICAD_CLI`` at it if it is not on PATH, e.g.
``KICAD_CLI="$HOME/.bin/kicad.AppImage kicad-cli"``.
"""

import os
import shlex
import shutil
import subprocess
from pathlib import Path

import cadquery as cq
import pytest

from skqyace010 import build
from skqyace010 import dims as d
from skqyace010 import model

FIXTURE = Path(__file__).parent / "kicad" / "skqyace010_fixture.kicad_pcb"
MODEL = Path(__file__).resolve().parents[1] / "models" / "SKQYACE010.step"
TOL = 0.05


def _kicad_cli() -> list[str] | None:
    if os.environ.get("KICAD_CLI"):
        return shlex.split(os.environ["KICAD_CLI"])
    found = shutil.which("kicad-cli")
    return [found] if found else None


@pytest.mark.skipif(_kicad_cli() is None, reason="kicad-cli not found (set KICAD_CLI)")
def test_kicad_exports_fixture_with_model(tmp_path):
    if not MODEL.exists():
        build.export(MODEL.parent)
    out = tmp_path / "fixture.step"
    result = subprocess.run(
        [
            *_kicad_cli(),
            "pcb", "export", "step",
            "--force",
            "--user-origin", "100x80mm",  # the footprint's position on the board
            "-o", str(out),
            str(FIXTURE),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    log = result.stdout + result.stderr
    assert result.returncode == 0, log
    assert "Could not" not in log and "not found" not in log.lower(), log

    solids = cq.importers.importStep(str(out)).solids().vals()
    boxes = [s.BoundingBox() for s in solids]
    board = max(boxes, key=lambda b: b.xlen * b.ylen)
    parts = [b for b in boxes if b is not board]
    # Base, cover, stem and two terminals, all above the board.
    assert len(parts) == len(model.PART_NAMES), [(b.xmin, b.xmax, b.zmin, b.zmax) for b in parts]
    seat = min(b.zmin for b in parts)
    assert seat >= board.zmax - 1e-6
    assert min(b.xmin for b in parts) == pytest.approx(-d.TERMINAL_SPAN / 2, abs=TOL)
    assert max(b.xmax for b in parts) == pytest.approx(d.TERMINAL_SPAN / 2, abs=TOL)
    assert max(b.zmax for b in parts) - seat == pytest.approx(d.HEIGHT, abs=TOL)
    # Terminals (the two parts that touch the seating plane at |x| > body/2)
    # lie inside the 2.0 x 1.0 lands.
    terminals = [b for b in parts if max(abs(b.xmin), abs(b.xmax)) > d.BODY_W / 2 + TOL]
    assert len(terminals) == 2
    for b in terminals:
        lo, hi = sorted((abs(b.xmin), abs(b.xmax)))
        assert d.PAD_X - d.PAD_L / 2 <= lo and hi <= d.PAD_X + d.PAD_L / 2
        assert max(abs(b.ymin), abs(b.ymax)) <= d.PAD_W / 2
