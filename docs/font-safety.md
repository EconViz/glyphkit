# Font safety and reproducibility

GlyphKit never searches the machine during ordinary `FontLibrary` construction. Supply font
paths, immutable bytes, or a binary stream. It snapshots the input once and identifies a face
by `(SHA-256 bytes, collection index)`, so relocating identical bytes does not change identity.

`discover_system_fonts()` is an explicit adapter. Freeze its result to a manifest, then restore
only through a resolver that verifies the recorded fingerprint. A manifest is an inventory, not
a bundle of font bytes.

Font source ingestion is bounded to 128 MiB. Empty, malformed, inaccessible, and oversized data
raise structured GlyphKit errors. GlyphKit does not access the network and does not silently
select an unconfigured system font.

## Portable embedding

`library.subset()` returns bytes and metadata. It never writes markup or a file. The policy is
mechanical rather than legal advice:

| Declared permission | Default result |
|---|---|
| Installable / editable | Allowed for the compatible use |
| Preview / print | Only non-editable preview/print output |
| Restricted | Rejected |
| Unknown or absent | Rejected unless `allow_unknown=True` |

The caller remains responsible for the font license and distribution rights. The optional
`portable` installation profile enables WOFF2; SFNT subsets are available in the base package.
