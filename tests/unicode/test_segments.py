from glyphkit.unicode import TextDirection, graphemes, text_direction


def test_graphemes_preserve_half_open_source_ranges() -> None:
    clusters = graphemes("A\u0301🙂")
    assert tuple((item.text, item.source_range.start, item.source_range.end) for item in clusters) == (
        ("A\u0301", 0, 2),
        ("🙂", 2, 3),
    )


def test_direction_uses_first_strong_character() -> None:
    assert text_direction("123 العربية") is TextDirection.RTL
    assert text_direction("English العربية") is TextDirection.LTR

