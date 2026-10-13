# Changelog

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
