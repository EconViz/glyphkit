from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "glyphkit"
FORBIDDEN_ROOTS = {
    "bezierkit",
    "kinetickit",
    "matplotlib",
    "mosaickit",
    "plotly",
    "utility_viz",
}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_package_never_imports_visualization_or_renderer_packages() -> None:
    violations = {
        str(path.relative_to(PACKAGE_ROOT)): sorted(imported_roots(path) & FORBIDDEN_ROOTS)
        for path in PACKAGE_ROOT.rglob("*.py")
        if imported_roots(path) & FORBIDDEN_ROOTS
    }
    assert violations == {}


def test_low_level_sources_do_not_import_higher_layers() -> None:
    forbidden = {"embedding", "layout", "math", "shaping", "unicode"}
    violations: dict[str, list[str]] = {}
    for path in (PACKAGE_ROOT / "sources").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                if len(parts) > 1 and parts[0] == "glyphkit":
                    imported.add(parts[1])
        if imported & forbidden:
            violations[str(path.relative_to(PACKAGE_ROOT))] = sorted(imported & forbidden)
    assert violations == {}


def test_font_catalog_does_not_import_text_processing_layers() -> None:
    forbidden = {"embedding", "layout", "math", "shaping", "unicode"}
    violations: dict[str, list[str]] = {}
    for path in (PACKAGE_ROOT / "fonts").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                if len(parts) > 1 and parts[0] == "glyphkit":
                    imported.add(parts[1])
        if imported & forbidden:
            violations[str(path.relative_to(PACKAGE_ROOT))] = sorted(imported & forbidden)
    assert violations == {}
