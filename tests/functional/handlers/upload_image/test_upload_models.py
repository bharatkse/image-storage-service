"""Unit tests for upload request validation."""

import base64

from pydantic import ValidationError
import pytest

from core.utils.constants import MAX_FILE_SIZE
from handlers.upload_image.models import ImageUploadRequest


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def valid_payload(**overrides):
    payload = {
        "file": b64(b"test-image"),
        "user_id": "john_doe",
        "image_name": "photo.jpg",
        "description": "Nice photo",
        "tags": "beach,sunset",
    }
    payload.update(overrides)
    return payload


class TestUploadModels:
    """Upload request validation tests."""

    def test_valid_request(self) -> None:
        req = ImageUploadRequest(**valid_payload())
        assert req.user_id == "john_doe"
        assert req.image_name == "photo.jpg"
        assert req.tags == ["beach", "sunset"]

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(user_id="john_doe")

    def test_invalid_user_id_characters(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(user_id="user@123"))

    def test_user_id_too_short(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(user_id="ab"))

    def test_user_id_with_uppercase_allowed(self) -> None:
        req = ImageUploadRequest(**valid_payload(user_id="John_Doe"))
        assert req.user_id == "John_Doe"

    def test_invalid_base64_string(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(file="invalid!!"))

    def test_empty_base64_string(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(file=""))

    def test_base64_decodes_to_empty_bytes(self) -> None:
        empty_b64 = base64.b64encode(b"").decode()
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(file=empty_b64))

    def test_file_size_exact_limit_allowed(self) -> None:
        req = ImageUploadRequest(**valid_payload(file=b64(b"a" * MAX_FILE_SIZE)))
        assert req is not None

    def test_file_size_exceeded(self) -> None:
        oversized = b"a" * (50 * 1024 * 1024 + 1)
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(file=b64(oversized)))

    def test_image_name_without_extension(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(image_name="photo"))

    def test_image_name_with_uppercase_extension(self) -> None:
        req = ImageUploadRequest(**valid_payload(image_name="photo.JPG"))
        assert req.image_name.lower().endswith(".jpg")

    def test_image_name_multiple_dots(self) -> None:
        req = ImageUploadRequest(**valid_payload(image_name="my.photo.v1.png"))
        assert req.image_name.endswith(".png")

    def test_image_name_invalid_extension(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(image_name="photo.exe"))

    def test_tags_string_normalization(self) -> None:
        req = ImageUploadRequest(**valid_payload(tags=" beach , sunset , "))
        assert req.tags == ["beach", "sunset"]

    def test_tags_list_normalization(self) -> None:
        req = ImageUploadRequest(**valid_payload(tags=[" beach ", "sunset"]))
        assert req.tags == ["beach", "sunset"]

    def test_empty_tags_string(self) -> None:
        req = ImageUploadRequest(**valid_payload(tags=" , , "))
        assert req.tags == []

    def test_duplicate_tags_removed(self) -> None:
        req = ImageUploadRequest(**valid_payload(tags="beach,beach,sunset"))
        assert req.tags == ["beach", "sunset"]

    def test_max_tags_exceeded(self) -> None:
        tags = ",".join(f"tag{i}" for i in range(11))
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(tags=tags))

    def test_tags_invalid_type(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(tags=123))

    def test_description_exact_max_length(self) -> None:
        req = ImageUploadRequest(**valid_payload(description="x" * 1000))
        assert req.description

    def test_description_too_long(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(**valid_payload(description="x" * 1001))

    def test_description_only_spaces(self) -> None:
        req = ImageUploadRequest(**valid_payload(description="   "))
        assert req.description == ""
