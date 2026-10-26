# Changelog

## 1.0.0b5 — 2026-10-26

- `import glyphkit` no longer loads `fontTools.subset` and `fontTools.varLib.instancer`; they load
  the first time fonts are subset for embedding. Importing `glyphkit` or `glyphkit.math.layout`
  takes about 55 ms less (best of 7: 0.156 s to 0.101 s on one machine, 0.018 s of it the bare
  interpreter). Behaviour and the public API are unchanged. A test checks the modules stay unloaded.
- `glyphkit.math.layout` is now a package of small modules (model, metrics, spacing, shapes,
  engine, api) instead of one 889-line file. Every name it defined is still importable from
  `glyphkit.math.layout`; layouts are unchanged. A test now fails when any file under `src/`
  exceeds 450 lines.

## 1.0.0b4 — 2026-10-22

- A font is parsed once and kept (the eight most recently used, keyed by the SHA-256 of the font
  bytes and the face index), instead of once per glyph outline and once per math layout. With TeX
  Gyre Pagella Math one figure's 15 glyph outlines and four math layouts took about 210 ms and now
  take one parse; a larger font gains more. Outlines and layouts are identical. The parsed font
  is shared under a lock, so concurrent reads stay deterministic.

## 1.0.0b3 — 2026-10-21

- Math layout follows TeX's rules with the font's MATH constants. Fractions set their parts at full
  size in display style and clear the rule by the font's minimum gaps; scripts keep the minimum
  gaps, and script sizes derive from the whole expression; big operators are enlarged and centred on
  the axis in display style, with limits that clear them (and scripts at the side in text style and
  for integrals); radical signs and `\left...\right` delimiters stretch to their content; accents
  sit on their body; `\overline` and `\underline` are rules.
- Atoms are spaced by TeX's table (thin, medium and thick spaces around operators, relations and
  punctuation), and a binary operator with no left operand is ordinary. `-` as a binary operator is
  drawn as U+2212 when the font has it.
- `MathStyle.level` accepts `"text"` and `"scriptscript"` besides `"display"` and `"script"`.
  Constants scale with the size a box is set at, and a missing constant now falls back in points
  rather than being scaled a second time.
- More commands: the rest of the Greek alphabet, symbols and relations (`\le`, `\cdot`, `\infty`,
  `\partial`, `\to`, and more), functions (`\sin`, `\ln`, ...), `\mathrm`, `\text`,
  `\operatorname`, spaces (`\,` `\;` `\quad`), integrals, and more large operators.
- `Symbol.role` values `binary`, `relation`, `open`, `close`, `punct`, `integral`, `function` and
  `upright` classify atoms; the earlier role `operator` is still read. New `Space` node.
- New `MathStyle` constant overrides for the added constants (`LowerLimitGapMin`, ...).

## 1.0.0b2 — 2026-10-13

- `MathStyle` accepts `script_scale` and `script_script_scale` to override the font's
  `ScriptPercentScaleDown` and `ScriptScriptPercentScaleDown` constants.
- `MathStyle(constants=...)` overrides other OpenType MATH constants by name, in em, for fonts
  whose MATH table is incomplete.
- `MathStyle(letter_slant=...)` draws alphabetic symbols with the italic or oblique face of the
  same family instead of requiring the Unicode mathematical italic alphabet.
- Glyph ids from a companion face are no longer looked up in the MATH font's italic-correction
  and accent tables.

## 1.0.0b1 — 2026-10-12

First integration beta of the stable public typography contract.

- deterministic explicit font sources, matching, fallback, and manifests;
- Unicode segmentation, bidi-aware shaping, paragraph layout, measurements, and outlines;
- structured OpenType MATH layout and permission-aware portable subsets;
- versioned ordinary-data serialization and consumer-facing typography protocol;
- no rendering, animation, system-font scanning by default, network access, or output-file API.

## 0.x

Development-only internal milestones. They were not published as user releases.
