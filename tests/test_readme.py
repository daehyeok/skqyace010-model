"""The README embeds only images that the build generates.

Spec: skqyace010-model, "Provenance and licence documentation".
"""

import re
from pathlib import Path

from skqyace010 import build

ROOT = Path(__file__).resolve().parents[1]
# Markdown ![alt](target) and HTML <img src="target">.
_MD_IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)")
_HTML_IMAGE = re.compile(r"<img\b[^>]*\bsrc=[\"'](?P<src>[^\"']+)", re.I)

GENERATED_IMAGES = {f"models/{build.BASENAME}.png"}


def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_images_are_generated_and_committed():
    text = _readme()
    srcs = [m.group("src") for m in _MD_IMAGE.finditer(text)]
    srcs += [m.group("src") for m in _HTML_IMAGE.finditer(text)]
    assert srcs, "README embeds no image"
    for src in srcs:
        assert src in GENERATED_IMAGES, f"README image {src!r} is not a build output"
        assert (ROOT / src).is_file(), f"README image {src!r} does not exist"


def test_readme_render_is_above_provenance_with_alt_text():
    text = _readme()
    m = _MD_IMAGE.search(text)
    assert m and m.group("src") == f"models/{build.BASENAME}.png"
    assert "SKQYACE010" in m.group("alt")
    assert m.start() < text.index("## Provenance")
