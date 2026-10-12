"""Pinned python-bidi adapter retaining original indices."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from bidi.algorithm import (
    explicit_embed_and_overrides,
    get_base_level,
    get_embedding_levels,
    get_empty_storage,
    resolve_implicit_levels,
    resolve_neutral_types,
    resolve_weak_types,
)

from glyphkit.unicode.models import BidiLevel, TextDirection

T = TypeVar("T")


def resolve_bidi_levels(
    text: str, *, base_direction: TextDirection | None = None
) -> tuple[BidiLevel, ...]:
    if not text:
        return ()
    storage = get_empty_storage()
    base_level = (
        get_base_level(text)
        if base_direction is None
        else (1 if base_direction is TextDirection.RTL else 0)
    )
    storage["base_level"] = base_level
    storage["base_dir"] = "R" if base_level else "L"
    get_embedding_levels(text, storage)
    for index, character in enumerate(storage["chars"]):
        character["source_index"] = index
    explicit_embed_and_overrides(storage)
    resolve_weak_types(storage)
    resolve_neutral_types(storage, False)
    resolve_implicit_levels(storage, False)
    levels = {int(item["source_index"]): int(item["level"]) for item in storage["chars"]}
    return tuple(BidiLevel(index, levels.get(index, base_level)) for index in range(len(text)))


def reorder_line(items: Sequence[T], levels: Sequence[int | BidiLevel]) -> tuple[T, ...]:
    if len(items) != len(levels):
        raise ValueError("items and bidi levels must have equal length")
    numeric = [item.level if isinstance(item, BidiLevel) else item for item in levels]
    result = list(items)
    if not numeric:
        return ()
    maximum = max(numeric)
    odd_levels = [level for level in numeric if level % 2]
    if not odd_levels:
        return tuple(result)
    minimum_odd = min(odd_levels)
    for level in range(maximum, minimum_odd - 1, -1):
        start = 0
        while start < len(result):
            while start < len(result) and numeric[start] < level:
                start += 1
            end = start
            while end < len(result) and numeric[end] >= level:
                end += 1
            result[start:end] = reversed(result[start:end])
            numeric[start:end] = reversed(numeric[start:end])
            start = end
    return tuple(result)
