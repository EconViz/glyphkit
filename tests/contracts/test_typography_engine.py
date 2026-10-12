from glyphkit import FontLibrary, FontSource
from glyphkit.protocols import TypographyEngine
from tests.helpers import make_test_font


def test_static_and_animated_consumers_depend_only_on_protocol() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Contract"), label="contract"),)
    )
    assert isinstance(library, TypographyEngine)

    def static_consumer(engine: TypographyEngine) -> str:
        return type(engine).__name__

    def animated_consumer(engine: TypographyEngine) -> bool:
        return not hasattr(engine, "timeline") and not hasattr(engine, "animate")

    assert static_consumer(library) == "FontLibrary"
    assert animated_consumer(library)
