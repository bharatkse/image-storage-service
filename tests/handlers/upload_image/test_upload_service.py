import base64
from unittest.mock import patch

import pytest
from core.models.errors import (
    DuplicateImageError,
    ImageUploadFailedError,
    MetadataOperationFailedError,
    ValidationError,
)
from handlers.upload_image.service import UploadService


def fake_image_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\nfake-image-data"


class TestUploadService:
    def test_generate_image_id(self) -> None:
        id1 = UploadService.generate_image_id()
        id2 = UploadService.generate_image_id()

        assert id1.startswith("img_")
        assert id2.startswith("img_")
        assert id1 != id2

    def test_decode_file_valid(self) -> None:
        raw = b"image-bytes"
        encoded = base64.b64encode(raw).decode()

        assert UploadService.decode_file(encoded) == raw

    def test_decode_file_invalid(self) -> None:
        with pytest.raises(ValidationError):
            UploadService.decode_file("not-base64!!!")

    @patch("handlers.upload_image.service.detect_mime_type", return_value="image/png")
    def test_upload_image_success(self, mock_detect) -> None:
        service = UploadService()

        with (
            patch.object(service.metadata, "check_duplicate_image", return_value=False),
            patch.object(
                service.storage, "upload_image", return_value="images/u/img.png"
            ),
            patch.object(service.metadata, "create_metadata"),
        ):
            result = service.upload_image(
                user_id="user_1",
                image_name="photo.png",
                file_data=fake_image_bytes(),
                description="test image",
                tags=["a", "b"],
            )

        assert result["user_id"] == "user_1"
        assert result["image_name"] == "photo.png"
        assert result["mime_type"] == "image/png"
        assert result["s3_key"] == "images/u/img.png"
        assert result["file_size"] > 0
        assert "created_at" in result
        assert "file_hash" in result

    @patch(
        "handlers.upload_image.service.detect_mime_type",
        return_value="application/pdf",
    )
    def test_upload_rejects_unsupported_mime_type(self, mock_detect) -> None:
        service = UploadService()

        with pytest.raises(ValidationError):
            service.upload_image(
                user_id="user_1",
                image_name="file.pdf",
                file_data=b"%PDF",
            )

    @patch("handlers.upload_image.service.detect_mime_type", return_value=None)
    def test_upload_rejects_unknown_mime_type(self, mock_detect) -> None:
        service = UploadService()

        with pytest.raises(ValidationError):
            service.upload_image(
                user_id="user_1",
                image_name="file.bin",
                file_data=fake_image_bytes(),
            )

    @patch("handlers.upload_image.service.detect_mime_type", return_value="image/png")
    def test_upload_duplicate_image_same_user(self, mock_detect) -> None:
        service = UploadService()

        with patch.object(
            service.metadata,
            "check_duplicate_image",
            return_value=True,
        ):
            with pytest.raises(DuplicateImageError):
                service.upload_image(
                    user_id="user_1",
                    image_name="photo.png",
                    file_data=fake_image_bytes(),
                )

    @patch("handlers.upload_image.service.detect_mime_type", return_value="image/png")
    def test_upload_s3_failure(self, mock_detect) -> None:
        service = UploadService()

        with (
            patch.object(service.metadata, "check_duplicate_image", return_value=False),
            patch.object(
                service.storage,
                "upload_image",
                side_effect=Exception("S3 down"),
            ),
        ):
            with pytest.raises(ImageUploadFailedError):
                service.upload_image(
                    user_id="user_1",
                    image_name="photo.png",
                    file_data=fake_image_bytes(),
                )

    @patch("handlers.upload_image.service.detect_mime_type", return_value="image/png")
    def test_db_failure_triggers_s3_cleanup(self, mock_detect) -> None:
        service = UploadService()

        with (
            patch.object(service.metadata, "check_duplicate_image", return_value=False),
            patch.object(
                service.storage, "upload_image", return_value="images/u/img.png"
            ),
            patch.object(
                service.metadata,
                "create_metadata",
                side_effect=Exception("DB down"),
            ),
            patch.object(service.storage, "remove_image") as mock_cleanup,
        ):
            with pytest.raises(MetadataOperationFailedError):
                service.upload_image(
                    user_id="user_1",
                    image_name="photo.png",
                    file_data=fake_image_bytes(),
                )

        mock_cleanup.assert_called_once()

    @patch("handlers.upload_image.service.detect_mime_type", return_value="image/png")
    def test_cleanup_failure_does_not_mask_metadata_error(self, mock_detect) -> None:
        service = UploadService()

        with (
            patch.object(service.metadata, "check_duplicate_image", return_value=False),
            patch.object(
                service.storage, "upload_image", return_value="images/u/img.png"
            ),
            patch.object(
                service.metadata,
                "create_metadata",
                side_effect=Exception("DB down"),
            ),
            patch.object(
                service.storage,
                "remove_image",
                side_effect=Exception("Cleanup failed"),
            ),
        ):
            with pytest.raises(MetadataOperationFailedError):
                service.upload_image(
                    user_id="user_1",
                    image_name="photo.png",
                    file_data=fake_image_bytes(),
                )
