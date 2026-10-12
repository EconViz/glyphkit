"""FontTools Unicode script-data adapter."""

from __future__ import annotations

from fontTools import unicodedata as fonttools_unicode

from glyphkit.diagnostics import SourceRange
from glyphkit.unicode.models import RunSegment


def script_runs(text: str) -> tuple[RunSegment, ...]:
    if not text:
        return ()
    scripts = [fonttools_unicode.script(character) for character in text]
    inherited = {"Zyyy", "Zinh", "Zzzz"}
    last_specific: str | None = None
    for index, script in enumerate(scripts):
        if script in inherited:
            if last_specific is not None:
                scripts[index] = last_specific
        else:
            last_specific = script
    next_specific: str | None = None
    for index in range(len(scripts) - 1, -1, -1):
        if scripts[index] in inherited:
            if next_specific is not None:
                scripts[index] = next_specific
        else:
            next_specific = scripts[index]
    runs: list[RunSegment] = []
    start = 0
    for index in range(1, len(text) + 1):
        if index == len(text) or scripts[index] != scripts[start]:
            runs.append(RunSegment(text[start:index], SourceRange(start, index), scripts[start]))
            start = index
    return tuple(runs)
