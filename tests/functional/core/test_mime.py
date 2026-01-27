import pytest

from core.utils.mime import detect_mime_type


def test_detect_jpeg() -> None:
    assert detect_mime_type(b"\xff\xd8\xff\xe0abc") == "image/jpeg"


def test_detect_png() -> None:
    assert detect_mime_type(b"\x89PNG\r\n\x1a\nxxx") == "image/png"


def test_unsupported_type() -> None:
    with pytest.raises(ValueError):
        detect_mime_type(b"random-bytes")
