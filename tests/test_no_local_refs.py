"""No committed file references the machine-local datasheet directory.

Spec: skqyace010-model, "No reference to the machine-local datasheet
directory". The directory holds the vendor datasheet and STEP on one machine
only and is excluded by ``.gitignore``; that ignore rule is the only file
allowed to name it.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Built at runtime so this file does not match itself.
DIR_NAME = "lo" + "cal"
# The directory name followed by "/" at a path boundary: not part of
# ".dir-locals.el", "local_settings.py" or "*.local.md".
PATTERN = re.compile(r"(?<![\w.\-])" + DIR_NAME + "/")

SKIP_DIRS = {
    DIR_NAME,  # the directory itself (top level only, see _scanned_files)
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}
SKIP_PATHS = {
    Path(".gitignore"),  # the one allowed reference
    Path("openspec/changes"),  # history and in-flight change text
}
SKIP_SUFFIXES = {".step", ".stl", ".pdf", ".pyc", ".png", ".jpg", ".zip"}


def _scanned_files():
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == DIR_NAME:
            continue
        if any(part in SKIP_DIRS - {DIR_NAME} for part in rel.parts):
            continue
        if any(rel == p or p in rel.parents for p in SKIP_PATHS):
            continue
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield rel, path


def test_no_local_dir_references():
    hits = []
    for rel, path in _scanned_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if PATTERN.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    assert not hits, "References to the machine-local directory:\n" + "\n".join(hits)


def test_local_dir_is_git_ignored():
    rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert f"/{DIR_NAME}/" in rules
