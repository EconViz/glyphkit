from glyphkit.unicode import line_break_opportunities, script_runs


def test_script_runs_attach_common_punctuation_to_context() -> None:
    runs = script_runs("Latin,中文")
    assert tuple((run.text, run.script) for run in runs) == (("Latin,", "Latn"), ("中文", "Hani"))


def test_line_breaks_use_unicode_boundaries() -> None:
    assert line_break_opportunities("hello world") == (6, 11)
