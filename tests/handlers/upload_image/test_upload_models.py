"""Unit tests for upload handler."""

import base64

import pytest
from handlers.upload_image.models import ImageUploadRequest
from pydantic import ValidationError


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


class TestUploadModels:
    """Test upload request validation."""

    def test_valid_upload_request(self) -> None:
        data = {
            "file": base64.b64encode(b"test image data").decode(),
            "user_id": "john_doe",
            "image_name": "photo.jpg",
            "description": "My photo",
            "tags": "vacation,beach",
        }
        request = ImageUploadRequest(**data)
        assert request.user_id == "john_doe"
        assert request.image_name == "photo.jpg"

    def test_missing_required_field(self) -> None:
        data = {
            "file": base64.b64encode(b"test").decode(),
            "user_id": "john_doe",
            # Missing image_name
        }
        with pytest.raises(ValidationError):
            ImageUploadRequest(**data)

    def test_invalid_user_id_pattern(self) -> None:
        data = {
            "file": base64.b64encode(b"test").decode(),
            "user_id": "user@invalid",  # Invalid characters
            "image_name": "test.jpg",
        }
        with pytest.raises(ValidationError):
            ImageUploadRequest(**data)

    def test_user_id_too_short(self) -> None:
        data = {
            "file": base64.b64encode(b"test").decode(),
            "user_id": "ab",  # Less than 3 chars
            "image_name": "test.jpg",
        }
        with pytest.raises(ValidationError):
            ImageUploadRequest(**data)

    def test_max_tags_exceeded(self) -> None:
        data = {
            "file": base64.b64encode(b"test").decode(),
            "user_id": "john_doe",
            "image_name": "test.jpg",
            "tags": ",".join([f"tag{i}" for i in range(11)]),  # 11 tags
        }
        with pytest.raises(ValidationError):
            ImageUploadRequest(**data)

    def test_invalid_base64(self) -> None:
        data = {
            "file": "not-valid-base64!!!",
            "user_id": "john_doe",
            "image_name": "test.jpg",
        }
        with pytest.raises(ValidationError):
            ImageUploadRequest(**data)

    def test_valid_upload_request_with_string_tags(self) -> None:
        req = ImageUploadRequest(
            file=_b64(b"test"),
            user_id="john_doe",
            image_name="photo.jpg",
            description="desc",
            tags="vacation, beach , sunset",
        )
        assert req.tags == ["vacation", "beach", "sunset"]

    def test_valid_upload_request_with_list_tags(self) -> None:
        req = ImageUploadRequest(
            file=_b64(b"test"),
            user_id="john_doe",
            image_name="photo.jpg",
            tags=[" vacation ", "beach"],
        )
        assert req.tags == ["vacation", "beach"]

    def test_empty_tags_string(self) -> None:
        req = ImageUploadRequest(
            file=_b64(b"test"),
            user_id="john_doe",
            image_name="photo.jpg",
            tags=" , , ",
        )
        assert req.tags == []

    def test_tags_invalid_type(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(
                file=_b64(b"test"),
                user_id="john_doe",
                image_name="photo.jpg",
                tags=123,
            )

    def test_image_name_without_extension(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(
                file=_b64(b"test"),
                user_id="john_doe",
                image_name="photo",
            )

    def test_description_too_long(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(
                file=_b64(b"test"),
                user_id="john_doe",
                image_name="photo.jpg",
                description="x" * 1001,
            )

    def test_file_size_exceeded(self) -> None:
        big_data = b"a" * (51 * 1024 * 1024)  # 51MB
        with pytest.raises(ValidationError):
            ImageUploadRequest(
                file=_b64(big_data),
                user_id="john_doe",
                image_name="photo.jpg",
            )

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            ImageUploadRequest(
                file=_b64(b"test"),
                user_id="john_doe",
            )
