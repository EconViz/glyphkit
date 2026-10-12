"""Backend-neutral glyph shaping and fallback coordination."""

from glyphkit.shaping.models import GlyphRun, PositionedGlyph, ShapingStyle
from glyphkit.shaping.shape import shape_text

__all__ = ["GlyphRun", "PositionedGlyph", "ShapingStyle", "shape_text"]
