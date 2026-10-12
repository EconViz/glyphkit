from glyphkit.unicode import TextDirection, reorder_line, resolve_bidi_levels


def test_bidi_levels_retain_every_original_codepoint_index() -> None:
    text = "ABC العربية 123"
    levels = resolve_bidi_levels(text)
    assert tuple(item.source_index for item in levels) == tuple(range(len(text)))
    assert any(item.direction is TextDirection.RTL for item in levels)


def test_line_reorder_uses_resolved_levels_without_mutating_input() -> None:
    items = ("A", "ב", "ג", "B")
    assert reorder_line(items, (0, 1, 1, 0)) == ("A", "ג", "ב", "B")
    assert items == ("A", "ב", "ג", "B")
