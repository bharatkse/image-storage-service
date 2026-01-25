import pytest
from core.models.errors import (
    MetadataOperationFailedError,
    NotFoundError,
)
from handlers.get_image.service import GetService


class TestGetService:
    def test_generate_image_url_view_success(
        self,
        dynamodb_table,
        dynamodb_put_item,
        s3_bucket,
        s3_put_object,
        sample_jpeg_binary,
    ) -> None:
        item = {
            "image_id": "img_abc123",
            "user_id": "john_doe",
            "image_name": "photo.jpg",
            "created_at": "2024-01-15T10:00:00+00:00",
            "file_size": len(sample_jpeg_binary),
            "mime_type": "image/jpeg",
            "s3_key": "images/john_doe/img_abc123.jpg",
        }

        dynamodb_put_item(item)
        s3_put_object(
            key=item["s3_key"],
            body=sample_jpeg_binary,
            content_type="image/jpeg",
        )

        service = GetService()
        url, metadata = service.generate_image_url("img_abc123")

        assert isinstance(url, str)
        assert url.startswith("http")
        assert metadata["image_id"] == "img_abc123"

    def test_generate_image_url_download_mode_sets_attachment(
        self,
        dynamodb_table,
        dynamodb_put_item,
        s3_bucket,
    ) -> None:
        dynamodb_put_item(
            {
                "image_id": "img_dl",
                "user_id": "john",
                "image_name": "download.jpg",
                "created_at": "2024-01-01T10:00:00Z",
                "s3_key": "images/john/img_dl.jpg",
            }
        )

        service = GetService()
        url, _ = service.generate_image_url(
            "img_dl",
            mode="download",
        )

        assert "response-content-disposition=attachment" in url

    def test_generate_image_url_metadata_not_found(
        self,
        dynamodb_table,
    ) -> None:
        service = GetService()

        with pytest.raises(NotFoundError, match="Image not found"):
            service.generate_image_url("img_missing")

    def test_generate_image_url_missing_s3_key(
        self,
        dynamodb_table,
        dynamodb_put_item,
    ) -> None:
        dynamodb_put_item(
            {
                "image_id": "img_no_key",
                "user_id": "john",
                "created_at": "2024-01-01T10:00:00Z",
                "s3_key": None,
            }
        )

        service = GetService()

        with pytest.raises(MetadataOperationFailedError):
            service.generate_image_url("img_no_key")

    def test_generate_image_url_s3_bucket_missing(
        self,
        dynamodb_table,
        dynamodb_put_item,
        monkeypatch,
    ) -> None:
        """
        Pre-signed URL generation fails if S3 client errors.
        """
        dynamodb_put_item(
            {
                "image_id": "img_s3_fail",
                "user_id": "john",
                "created_at": "2024-01-01T10:00:00Z",
                "s3_key": "images/john/img_s3_fail.jpg",
            }
        )

        service = GetService()

        def boom(**_):
            raise RuntimeError("S3 down")

        monkeypatch.setattr(
            service.storage,
            "generate_presigned_get_url",
            boom,
        )

        with pytest.raises(MetadataOperationFailedError):
            service.generate_image_url("img_s3_fail")

    def test_get_metadata_only_success(
        self,
        dynamodb_table,
        dynamodb_put_item,
    ) -> None:
        item = {
            "image_id": "img_meta",
            "user_id": "john_doe",
            "image_name": "meta.jpg",
            "created_at": "2024-01-01T10:00:00Z",
            "s3_key": "images/john_doe/img_meta.jpg",
            "file_size": 10,
            "mime_type": "image/jpeg",
        }

        dynamodb_put_item(item)

        service = GetService()
        metadata = service.get_metadata("img_meta")

        assert metadata is not None
        assert metadata["image_id"] == "img_meta"

    def test_get_metadata_not_found_returns_none(
        self,
        dynamodb_table,
    ) -> None:
        service = GetService()

        assert service.get_metadata("missing") is None

    def test_get_metadata_invalid_format_raises(
        self,
        monkeypatch,
    ) -> None:
        service = GetService()

        monkeypatch.setattr(
            service.metadata,
            "fetch_metadata",
            lambda image_id: "not-a-dict",
        )

        with pytest.raises(MetadataOperationFailedError):
            service.get_metadata("img_bad")
