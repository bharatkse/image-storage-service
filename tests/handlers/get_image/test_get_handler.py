"""
Integration-style tests for get image Lambda handler.
Uses real GetService with moto-backed DynamoDB and S3.
"""

import json

from handlers.get_image.handler import handler


class TestGetImageHandler:
    def test_get_image_success(
        self,
        lambda_context,
        dynamodb_put_item,
        s3_put_object,
        sample_jpeg_binary,
    ) -> None:
        item = {
            "image_id": "img_abc123",
            "user_id": "john_doe",
            "image_name": "photo.jpg",
            "description": "My photo",
            "tags": ["test"],
            "created_at": "2024-01-15T10:00:00+00:00",
            "file_size": len(sample_jpeg_binary),
            "mime_type": "image/jpeg",
            "s3_key": "images/john_doe/img_abc123.jpg",
        }

        dynamodb_put_item(item)
        s3_put_object(item["s3_key"], sample_jpeg_binary, "image/jpeg")

        event = {
            "pathParameters": {"image_id": "img_abc123"},
            "queryStringParameters": None,
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["image_id"] == "img_abc123"
        assert body["mode"] == "view"
        assert body["url"].startswith("http")
        assert "metadata" not in body

    def test_get_image_with_metadata(
        self,
        lambda_context,
        dynamodb_put_item,
        s3_put_object,
        sample_jpeg_binary,
    ) -> None:
        item = {
            "image_id": "img_meta",
            "user_id": "john_doe",
            "image_name": "meta.jpg",
            "description": None,
            "tags": None,
            "created_at": "2024-01-15T10:00:00+00:00",
            "file_size": len(sample_jpeg_binary),
            "mime_type": "image/jpeg",
            "s3_key": "images/john_doe/img_meta.jpg",
        }

        dynamodb_put_item(item)
        s3_put_object(item["s3_key"], sample_jpeg_binary, "image/jpeg")

        event = {
            "pathParameters": {"image_id": "img_meta"},
            "queryStringParameters": {"metadata": "true"},
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        metadata = body["metadata"]

        assert metadata["image_id"] == "img_meta"
        assert metadata["image_name"] == "meta.jpg"
        assert metadata["user_id"] == "john_doe"
        assert metadata["mime_type"] == "image/jpeg"

    def test_get_image_download_mode(
        self,
        lambda_context,
        dynamodb_put_item,
        s3_put_object,
        sample_jpeg_binary,
    ) -> None:
        item = {
            "image_id": "img_dl",
            "user_id": "john",
            "image_name": "dl.jpg",
            "created_at": "2024-01-01T10:00:00Z",
            "file_size": len(sample_jpeg_binary),
            "mime_type": "image/jpeg",
            "s3_key": "images/john/img_dl.jpg",
        }

        dynamodb_put_item(item)
        s3_put_object(item["s3_key"], sample_jpeg_binary, "image/jpeg")

        event = {
            "pathParameters": {"image_id": "img_dl"},
            "queryStringParameters": {"download": "true"},
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["mode"] == "download"
        assert body["url"].startswith("http")

    def test_get_image_not_found(
        self,
        lambda_context,
    ) -> None:
        event = {
            "pathParameters": {"image_id": "img_missing"},
            "queryStringParameters": None,
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"] == "INTERNAL_SERVER_ERROR"

    def test_get_missing_image_id(
        self,
        lambda_context,
    ) -> None:
        event = {
            "pathParameters": None,
            "queryStringParameters": None,
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422
        body = json.loads(response["body"])
        assert body["error"] == "VALIDATION_FAILED"

    def test_get_empty_image_id(
        self,
        lambda_context,
    ) -> None:
        event = {
            "pathParameters": {"image_id": ""},
            "queryStringParameters": None,
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422
        body = json.loads(response["body"])
        assert body["error"] == "VALIDATION_FAILED"

    def test_metadata_flag_case_insensitive(
        self,
        lambda_context,
        dynamodb_put_item,
        s3_put_object,
        sample_jpeg_binary,
    ) -> None:
        item = {
            "image_id": "img_flag",
            "user_id": "john",
            "image_name": "flag.jpg",
            "created_at": "2024-01-01T10:00:00Z",
            "file_size": len(sample_jpeg_binary),
            "mime_type": "image/jpeg",
            "s3_key": "images/john/img_flag.jpg",
        }

        dynamodb_put_item(item)
        s3_put_object(item["s3_key"], sample_jpeg_binary, "image/jpeg")

        event = {
            "pathParameters": {"image_id": "img_flag"},
            "queryStringParameters": {"metadata": "TRUE"},
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "metadata" in body
