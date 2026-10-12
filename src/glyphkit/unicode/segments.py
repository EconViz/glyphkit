"""Small adapter around Unicode segmentation data."""

from __future__ import annotations

import unicodedata

from uniseg.graphemecluster import grapheme_clusters

from glyphkit.diagnostics import SourceRange
from glyphkit.unicode.models import TextCluster, TextDirection


def graphemes(text: str) -> tuple[TextCluster, ...]:
    result: list[TextCluster] = []
    offset = 0
    for cluster in grapheme_clusters(text):
        end = offset + len(cluster)
        result.append(TextCluster(cluster, SourceRange(offset, end)))
        offset = end
    return tuple(result)


def text_direction(text: str) -> TextDirection:
    for character in text:
        bidi = unicodedata.bidirectional(character)
        if bidi in {"R", "AL", "RLE", "RLO", "RLI"}:
            return TextDirection.RTL
        if bidi in {"L", "LRE", "LRO", "LRI"}:
            return TextDirection.LTR
    return TextDirection.LTR

