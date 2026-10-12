import pytest

from glyphkit import FontLibrary, FontNotFoundError, FontQuery, FontSource
from tests.helpers import make_test_font


def library() -> FontLibrary:
    return FontLibrary.from_sources(
        (
            FontSource.bytes(make_test_font(family="Primary", weight=400), label="regular"),
            FontSource.bytes(make_test_font(family="Primary", weight=700), label="bold"),
            FontSource.bytes(make_test_font(family="Fallback", weight=400), label="fallback"),
        ),
        generic_families={"sans-serif": ("Primary", "Fallback")},
    )


def test_matches_family_weight_and_generic_alias_deterministically() -> None:
    fonts = library()
    assert fonts.match(FontQuery(("Primary",), weight=650)).face.weight == 700
    assert fonts.match(FontQuery(("sans-serif",))).face.family == "Primary"
    assert fonts.match(FontQuery(("primary",))).face.family == "Primary"


def test_unconfigured_family_never_uses_machine_fonts() -> None:
    with pytest.raises(FontNotFoundError):
        library().match(FontQuery(("Definitely Installed Somewhere",)))

