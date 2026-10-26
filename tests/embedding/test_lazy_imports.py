"""Font embedding machinery loads only when something is embedded."""

import subprocess
import sys
import textwrap

HEAVY = ("fontTools.subset", "fontTools.varLib.instancer")

SCRIPT = textwrap.dedent(
    """
    import sys

    from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
    from glyphkit.embedding import EmbeddingUse
    from glyphkit.math.layout import layout_math
    from tests.helpers import make_test_font

    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Lazy"), label="lazy"),)
    )
    layout = library.layout(Paragraph((TextSpan("A", TextStyle(("Lazy",), 18)),)))
    library.outline(layout.lines[0].runs[0].glyphs[0])
    heavy = {heavy!r}
    loaded = [name for name in heavy if name in sys.modules]
    print("BEFORE", loaded)
    bundle = library.subset(layout, embedding_use=EmbeddingUse.WEB)
    print("AFTER", [name for name in heavy if name in sys.modules], len(bundle.fonts[0].data))
    """
).format(heavy=HEAVY)


def test_subsetting_modules_load_only_when_embedding() -> None:
    result = subprocess.run(
        [sys.executable, "-c", SCRIPT], capture_output=True, text=True, check=True
    )
    lines = dict(line.split(" ", 1) for line in result.stdout.splitlines())
    assert lines["BEFORE"] == "[]"
    assert lines["AFTER"].startswith("['fontTools.subset', 'fontTools.varLib.instancer'")


def test_plain_import_does_not_load_subsetting_modules() -> None:
    code = (
        "import sys, glyphkit, glyphkit.math.layout\n"
        f"print([m for m in {HEAVY!r} if m in sys.modules])"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
