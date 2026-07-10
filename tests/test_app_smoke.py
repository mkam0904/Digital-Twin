# tests/test_app_smoke.py
"""Syntax gate: parse (don't run) every source file, so a stray character
in app.py fails CI instead of crashing the Space at startup."""

import py_compile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCES = [REPO_ROOT / "app.py"] + sorted((REPO_ROOT / "src").glob("*.py"))

def test_all_sources_compile():
    assert SOURCES, "No source files found — wrong repo layout?"
    for src in SOURCES:
        try:
            py_compile.compile(str(src), doraise=True)
        except py_compile.PyCompileError as e:
            raise AssertionError(f"{src.name}: syntax error:\n{e}") from e