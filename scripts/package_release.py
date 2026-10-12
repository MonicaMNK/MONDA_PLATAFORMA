#!/usr/bin/env python3
"""Create a clean GitHub-ready source ZIP and SHA-256 checksum."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT.parent
ZIP_PATH = OUT_DIR / "MONDA_PLATAFORMA_FINAL_GITHUB.zip"
SHA_PATH = OUT_DIR / "MONDA_PLATAFORMA_FINAL_GITHUB.sha256"
EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "htmlcov"}
EXCLUDED_NAMES = {".env", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".zip", ".db", ".sqlite", ".sqlite3"}


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path.name.endswith(".sha256"):
        return False
    if rel.parts[:2] == ("data", "uploads") and path.name != ".gitkeep":
        return False
    if rel.parts[:2] == ("data", "traces") and path.name != ".gitkeep":
        return False
    return path.is_file()


def main() -> None:
    files = sorted(p for p in ROOT.rglob("*") if should_include(p))
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as zf:
        for path in files:
            arcname = Path(ROOT.name) / path.relative_to(ROOT)
            zf.write(path, arcname.as_posix())
    digest = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
    SHA_PATH.write_text(f"{digest}  {ZIP_PATH.name}\n", encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH) as zf:
        bad = zf.testzip()
        if bad:
            raise SystemExit(f"ZIP verification failed at {bad}")
    print(f"ZIP: {ZIP_PATH}")
    print(f"SHA256: {digest}")
    print(f"Files: {len(files)}")


if __name__ == "__main__":
    main()
