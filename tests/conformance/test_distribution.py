import runpy
from pathlib import Path

from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle
from glyphkit.embedding import EmbeddingUse
from tests.helpers import make_test_font

ROOT = Path(__file__).parents[2]


def test_public_docs_examples_and_license_describe_data_only_contract() -> None:
    for path in (
        ROOT / "README.md",
        ROOT / "LICENSE",
        ROOT / "CHANGELOG.md",
        ROOT / "docs" / "font-safety.md",
        ROOT / "docs" / "math-grammar.md",
        ROOT / "examples" / "plain_text.py",
        ROOT / "examples" / "mixed_scripts.py",
        ROOT / "examples" / "math_layout.py",
        ROOT / "examples" / "consumer_adapter.py",
    ):
        assert path.is_file()
    readme = (ROOT / "README.md").read_text(encoding="utf-8").casefold()
    assert "does **not** draw" in readme
    assert "write svg" in readme
    for example in (ROOT / "examples").glob("*.py"):
        runpy.run_path(str(example))


def test_subset_is_data_only_and_never_creates_a_target_file(tmp_path) -> None:
    library = FontLibrary.from_sources(
        (FontSource.bytes(make_test_font(family="Conformance"), label="conformance"),)
    )
    layout = library.layout(Paragraph((TextSpan("AB", TextStyle(("Conformance",), 18)),)))
    bundle = library.subset(layout, embedding_use=EmbeddingUse.WEB)
    assert bundle.fonts[0].data
    assert list(tmp_path.iterdir()) == []
