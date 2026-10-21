from glyphkit import __version__


def test_beta_version_is_the_only_public_release_series() -> None:
    assert __version__ == "1.0.0b3"
