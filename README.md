# GlyphKit

GlyphKit is a renderer-independent Python typography engine. It selects explicit fonts,
shapes Unicode, lays out paragraphs and structured math, measures text, extracts exact
glyph paths, and creates permission-aware subset bytes. It returns immutable data only.

It does **not** draw, animate, create a canvas or scene, download fonts, interpret licenses,
or write SVG, HTML, images, video, PDFs, or any other output file. A static figure kit,
an animation kit, a document tool, or an application may consume the same `TextLayout`
without GlyphKit importing any of them.

## Install

```bash
uv add glyphkit
uv add 'glyphkit[portable]'  # add WOFF2 payload support
```

GlyphKit supports Python 3.10 through 3.13.

## Explicit fonts, one layout for any consumer

```python
from glyphkit import FontLibrary, FontSource, Paragraph, TextSpan, TextStyle

library = FontLibrary.from_sources(
    (
        FontSource.path("fonts/SourceSans3-Regular.ttf"),
        FontSource.path("fonts/NotoSansTC-Regular.otf"),
    ),
    generic_families={"sans-serif": ("Source Sans 3", "Noto Sans TC")},
)

paragraph = Paragraph(
    (TextSpan("效用 U(x₁, x₂)", TextStyle(("Source Sans 3", "Noto Sans TC"), 18)),),
    max_width=360,
)
layout = library.layout(paragraph)
```

`layout` is a data asset: its lines, runs, glyph positions, source ranges, logical bounds,
ink bounds, and font uses are independent of DPI and any output backend.

## Geometry, math, and portable data

```python
from glyphkit.embedding import EmbeddingUse
from glyphkit.math import MathStyle, parse_math

glyph = layout.lines[0].runs[0].glyphs[0]
outline = library.outline(glyph)  # MoveTo / LineTo / QuadraticTo / CubicTo / ClosePath
bundle = library.subset(layout, embedding_use=EmbeddingUse.WEB)  # bytes, never a file

formula = parse_math(r"U(x_1, x_2) = x_1^\\alpha x_2^{1-\\alpha}")
math_box = library.layout_math(formula, style=MathStyle(18, ("STIX Two Math",)))
```

See [font safety](docs/font-safety.md), the [supported math grammar](docs/math-grammar.md),
and the data-only [`examples/`](examples) directory.

## Reproducibility and safety

Use caller-owned paths, bytes, or streams. Paths and streams are snapshotted while building
the library; face identity derives from SHA-256 content plus collection index, not the path.
System discovery is opt-in. A portable subset is rejected when embedding permissions are
restricted or unknown unless the caller explicitly records an override.

GlyphKit is distributed under the [MIT License](LICENSE).
