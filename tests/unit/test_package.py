"""Phase 0 package smoke tests."""

from queryguard import __version__


def test_package_version() -> None:
    assert __version__ == "0.1.0"
