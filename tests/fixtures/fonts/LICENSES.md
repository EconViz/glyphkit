# Test font policy

GlyphKit does not store third-party font binaries in this repository. Tests construct small,
deterministic OpenType fixtures at runtime with FontTools under the repository's MIT license.
They are test data only and are never included in the wheel or source distribution.

Integration tests may opt into a locally installed system font, but never require one for CI.
