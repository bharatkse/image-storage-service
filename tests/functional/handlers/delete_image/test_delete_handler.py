import json
from typing import Any
from unittest.mock import patch

from botocore.exceptions import ClientError
import pytest

from handlers.delete_image.handler import handler


class TestDeleteImageHandler:
    def test_delete_image_success(
        self,
        lambda_context,
        dynamodb_table,
        dynamodb_put_item,
        s3_put_object,
        s3_get_object,
    ) -> None:
        metadata = {
            "image_id": "img_abc123",
            "user_id": "john_doe",
            "s3_key": "images/john_doe/img_abc123.jpg",
            "created_at": "2024-01-01T10:00:00Z",
            "file_size": 123,
            "mime_type": "image/jpeg",
        }

        dynamodb_put_item(metadata)
        s3_put_object(metadata["s3_key"], b"data", "image/jpeg")

        event: dict[str, Any] = {"pathParameters": {"image_id": "img_abc123"}}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["image_id"] == "img_abc123"
        assert body["s3_key"] == metadata["s3_key"]
        assert body["message"] == "Image deleted successfully"
        assert "deleted_at" in body

        # metadata deleted
        assert dynamodb_table.get_item(Key={"image_id": "img_abc123"}).get("Item") is None

        # s3 object deleted
        with pytest.raises(ClientError):
            s3_get_object(metadata["s3_key"])

    def test_delete_image_not_found(
        self,
        aws_mock,
        lambda_context,
        dynamodb_table,
        s3_bucket,
    ) -> None:
        event = {
            "pathParameters": {
                "image_id": "missing",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 404

        body = json.loads(response["body"])
        assert body["error"] == "NOT_FOUND"
        assert body["message"] == "Image not found: missing"

    def test_delete_missing_image_id(self, lambda_context) -> None:
        response = handler({"pathParameters": None}, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "BAD_REQUEST"

    def test_delete_empty_path_parameters(self, lambda_context) -> None:
        response = handler({"pathParameters": {}}, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "BAD_REQUEST"

    def test_delete_invalid_metadata_state(
        self,
        lambda_context,
        dynamodb_put_item,
    ) -> None:
        # s3_key missing
        dynamodb_put_item({"image_id": "img_bad"})

        response = handler(
            {"pathParameters": {"image_id": "img_bad"}},
            lambda_context,
        )

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "metadata" in body["message"].lower()

    def test_delete_s3_failure(
        self,
        lambda_context,
        dynamodb_put_item,
    ) -> None:
        dynamodb_put_item(
            {
                "image_id": "img_s3_fail",
                "s3_key": "images/u/img_s3_fail.jpg",
            }
        )

        with patch(
            "handlers.delete_image.service.S3ImageStorage.remove_image",
            side_effect=Exception("S3 down"),
        ):
            response = handler(
                {"pathParameters": {"image_id": "img_s3_fail"}},
                lambda_context,
            )

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "Unable to delete image from storage" in body["message"]

    def test_delete_metadata_failure_after_s3_delete(
        self,
        lambda_context,
        dynamodb_put_item,
    ) -> None:
        dynamodb_put_item(
            {
                "image_id": "img_db_fail",
                "s3_key": "images/u/img_db_fail.jpg",
            }
        )

        with patch(
            "handlers.delete_image.service.DynamoDBMetadata.remove_metadata",
            side_effect=Exception("DB down"),
        ):
            response = handler(
                {"pathParameters": {"image_id": "img_db_fail"}},
                lambda_context,
            )

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "metadata" in body["message"].lower()

    def test_delete_unexpected_exception(self, lambda_context) -> None:
        with patch(
            "handlers.delete_image.service.DeleteService.delete_image",
            side_effect=RuntimeError("boom"),
        ):
            response = handler(
                {"pathParameters": {"image_id": "img_1"}},
                lambda_context,
            )

        assert response["statusCode"] == 500
