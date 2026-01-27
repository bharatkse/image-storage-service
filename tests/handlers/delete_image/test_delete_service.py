from botocore.exceptions import ClientError
import pytest

from core.models.errors import (
    MetadataOperationFailedError,
    NotFoundError,
    S3Error,
)
from handlers.delete_image.service import DeleteService


class TestDeleteService:
    def test_delete_image_success(
        self,
        dynamodb_table,
        dynamodb_put_item,
        s3_put_object,
        s3_get_object,
    ) -> None:
        item = {
            "image_id": "img_123",
            "user_id": "john",
            "image_name": "photo.jpg",
            "created_at": "2024-01-01T10:00:00Z",
            "s3_key": "images/john/img_123.jpg",
            "file_size": 100,
            "mime_type": "image/jpeg",
        }

        dynamodb_put_item(item)
        s3_put_object(
            key=item["s3_key"],
            body=b"fake image bytes",
            content_type="image/jpeg",
        )

        service = DeleteService()
        result = service.delete_image("img_123")

        assert result["image_id"] == "img_123"
        assert result["s3_key"] == item["s3_key"]
        assert "deleted_at" in result

        # Metadata removed
        response = dynamodb_table.get_item(Key={"image_id": "img_123"})
        assert response.get("Item") is None

        # S3 object removed
        with pytest.raises(ClientError):
            s3_get_object(item["s3_key"])

    def test_delete_image_not_found(self, dynamodb_table) -> None:
        service = DeleteService()

        with pytest.raises(NotFoundError, match="Image not found"):
            service.delete_image("missing-id")

    def test_delete_image_missing_s3_key(
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

        service = DeleteService()

        with pytest.raises(MetadataOperationFailedError):
            service.delete_image("img_no_key")

    def test_delete_image_s3_failure(
        self,
        dynamodb_table,
        dynamodb_put_item,
        monkeypatch,
    ) -> None:
        dynamodb_put_item(
            {
                "image_id": "img_s3_fail",
                "user_id": "john",
                "created_at": "2024-01-01T10:00:00Z",
                "s3_key": "images/john/img_s3_fail.jpg",
            }
        )

        service = DeleteService()

        def fail_storage_delete(*_, **__):
            raise RuntimeError("S3 down")

        monkeypatch.setattr(
            service.storage,
            "remove_image",
            fail_storage_delete,
        )

        with pytest.raises(S3Error):
            service.delete_image("img_s3_fail")

    def test_delete_image_db_failure_after_s3_delete(
        self,
        dynamodb_table,
        dynamodb_put_item,
        s3_put_object,
        monkeypatch,
    ) -> None:
        item = {
            "image_id": "img_db_fail",
            "user_id": "john",
            "created_at": "2024-01-01T10:00:00Z",
            "s3_key": "images/john/img_db_fail.jpg",
        }

        dynamodb_put_item(item)
        s3_put_object(
            key=item["s3_key"],
            body=b"data",
            content_type="image/jpeg",
        )

        service = DeleteService()

        def fail_metadata_delete(*_, **__):
            raise RuntimeError("DB down")

        monkeypatch.setattr(
            service.metadata,
            "remove_metadata",
            fail_metadata_delete,
        )

        with pytest.raises(MetadataOperationFailedError):
            service.delete_image("img_db_fail")
