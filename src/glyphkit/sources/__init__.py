"""Explicit font sources and immutable byte snapshots."""

from glyphkit.sources.load import FontSnapshot, snapshot_source
from glyphkit.sources.models import MAX_FONT_BYTES, FontSource

__all__ = ["MAX_FONT_BYTES", "FontSnapshot", "FontSource", "snapshot_source"]
