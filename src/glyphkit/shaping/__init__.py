"""Backend-neutral glyph shaping and fallback coordination."""

from glyphkit.shaping.models import GlyphExtents, GlyphRun, PositionedGlyph, ShapingStyle
from glyphkit.shaping.shape import shape_text

__all__ = ["GlyphExtents", "GlyphRun", "PositionedGlyph", "ShapingStyle", "shape_text"]
