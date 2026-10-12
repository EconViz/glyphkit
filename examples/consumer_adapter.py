"""A consumer accepts the protocol and never needs GlyphKit renderer objects."""

from glyphkit import Paragraph, TextLayout, TypographyEngine


class DataOnlyConsumer:
    def __init__(self, typography: TypographyEngine) -> None:
        self._typography = typography

    def text_asset(self, paragraph: Paragraph) -> TextLayout:
        return self._typography.layout(paragraph)
