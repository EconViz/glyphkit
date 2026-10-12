from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
from tests.helpers import make_test_font


def test_measurement_keeps_logical_and_ink_contracts_distinct() -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Metrics"), label="metrics"),)
    )
    layout = library.layout(Paragraph((TextSpan("AB", TextStyle(("Metrics",), 20)),)))
    measurement = layout.measure()
    assert measurement.advance == 24
    assert measurement.logical_bounds.width == 24
    assert measurement.ink_bounds is layout.ink_bounds
    assert measurement.baselines == (0,)
