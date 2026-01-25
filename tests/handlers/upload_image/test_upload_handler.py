import base64
import json
from unittest.mock import patch

from core.models.errors import (
    DuplicateImageError,
    ImageUploadFailedError,
    MetadataOperationFailedError,
    ValidationError,
)
from core.utils.constants import MAX_FILE_SIZE
from handlers.upload_image.handler import handler


def valid_png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\nfake-image-data"


def large_png_bytes() -> bytes:
    size: int = int(MAX_FILE_SIZE)
    return b"\x89PNG\r\n\x1a\n" + b"x" * (size + 1)


class TestUploadHandler:
    @patch(
        "handlers.upload_image.service.DynamoDBMetadata.check_duplicate_image",
        return_value=False,
    )
    def test_upload_success(
        self,
        mock_duplicate,
        aws_mock,
        lambda_context,
        dynamodb_table,
        s3_bucket,
    ) -> None:
        event = {
            "body": json.dumps(
                {
                    "file": base64.b64encode(valid_png_bytes()).decode(),
                    "user_id": "user_1",
                    "image_name": "photo.png",
                    "tags": ["nature"],
                }
            )
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])

        assert body["user_id"] == "user_1"
        assert body["image_name"] == "photo.png"
        assert body["s3_key"].startswith("images/user_1/")
        assert body["message"] == "Image uploaded successfully"

    def test_upload_duplicate_image(
        self,
        lambda_context,
    ) -> None:
        with patch(
            "handlers.upload_image.service.UploadService.upload_image",
            side_effect=DuplicateImageError(message="This image already exists"),
        ):
            event = {
                "body": json.dumps(
                    {
                        "file": base64.b64encode(valid_png_bytes()).decode(),
                        "user_id": "user_1",
                        "image_name": "photo.png",
                    }
                )
            }

            response = handler(event, lambda_context)

        assert response["statusCode"] == 422
        body = json.loads(response["body"])
        assert body["error"] == "DUPLICATE_IMAGE_ERROR"

    def test_upload_invalid_base64(self, lambda_context) -> None:
        event = {
            "body": json.dumps(
                {
                    "file": "!!!invalid!!!",
                    "user_id": "user_1",
                    "image_name": "photo.png",
                }
            )
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422

    def test_upload_file_size_exceeded(self, lambda_context) -> None:
        event = {
            "body": json.dumps(
                {
                    "file": base64.b64encode(large_png_bytes()).decode(),
                    "user_id": "user_1",
                    "image_name": "big.png",
                }
            )
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422

    def test_upload_invalid_image_name(self, lambda_context) -> None:
        event = {
            "body": json.dumps(
                {
                    "file": base64.b64encode(valid_png_bytes()).decode(),
                    "user_id": "user_1",
                    "image_name": "photo",
                }
            )
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422

    def test_upload_invalid_json(self, lambda_context) -> None:
        response = handler({"body": "{bad-json"}, lambda_context)
        assert response["statusCode"] == 422

    def test_upload_empty_body(self, lambda_context) -> None:
        response = handler({"body": None}, lambda_context)
        assert response["statusCode"] == 422

    def test_upload_s3_failure(self, lambda_context) -> None:
        with patch(
            "handlers.upload_image.service.UploadService.upload_image",
            side_effect=ImageUploadFailedError(message="S3 down"),
        ):
            event = {
                "body": json.dumps(
                    {
                        "file": base64.b64encode(valid_png_bytes()).decode(),
                        "user_id": "user_1",
                        "image_name": "photo.png",
                    }
                )
            }

            response = handler(event, lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "S3 down" in body["message"]

    def test_upload_tags_as_string(self, aws_mock, lambda_context) -> None:
        event = {
            "body": json.dumps(
                {
                    "file": base64.b64encode(valid_png_bytes()).decode(),
                    "user_id": "user_1",
                    "image_name": "photo.png",
                    "tags": "a, b, c",
                }
            )
        }

        response = handler(event, lambda_context)
        assert response["statusCode"] == 201

    def test_upload_unsupported_mime_type(self, lambda_context) -> None:
        with patch(
            "handlers.upload_image.service.UploadService.upload_image",
            side_effect=ValidationError(message="Unsupported image type"),
        ):
            event = {
                "body": json.dumps(
                    {
                        "file": base64.b64encode(valid_png_bytes()).decode(),
                        "user_id": "user_1",
                        "image_name": "photo.png",
                    }
                )
            }

            response = handler(event, lambda_context)

        assert response["statusCode"] == 422
        body = json.loads(response["body"])
        assert body["error"] == "VALIDATION_ERROR"

    def test_upload_metadata_failure(self, lambda_context) -> None:
        with patch(
            "handlers.upload_image.service.UploadService.upload_image",
            side_effect=MetadataOperationFailedError(
                message="DB down",
                error_code="METADATA_CREATE_FAILED",
            ),
        ):
            event = {
                "body": json.dumps(
                    {
                        "file": base64.b64encode(valid_png_bytes()).decode(),
                        "user_id": "user_1",
                        "image_name": "photo.png",
                    }
                )
            }

            response = handler(event, lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "DB down" in body["message"]

    def test_upload_unexpected_exception(self, lambda_context) -> None:
        with patch(
            "handlers.upload_image.service.UploadService.upload_image",
            side_effect=RuntimeError("boom"),
        ):
            event = {
                "body": json.dumps(
                    {
                        "file": base64.b64encode(valid_png_bytes()).decode(),
                        "user_id": "user_1",
                        "image_name": "photo.png",
                    }
                )
            }

            response = handler(event, lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "Unexpected error occurred" in body["message"]

    def test_upload_decode_file_validation_error(self, lambda_context) -> None:
        with patch(
            "handlers.upload_image.service.UploadService.decode_file",
            side_effect=ValidationError(message="Invalid image data"),
        ):
            event = {
                "body": json.dumps(
                    {
                        "file": base64.b64encode(valid_png_bytes()).decode(),
                        "user_id": "user_1",
                        "image_name": "photo.png",
                    }
                )
            }

            response = handler(event, lambda_context)

        assert response["statusCode"] == 422

    def test_upload_missing_required_fields(self, lambda_context) -> None:
        event = {
            "body": json.dumps(
                {
                    "file": base64.b64encode(valid_png_bytes()).decode(),
                    # user_id missing
                    "image_name": "photo.png",
                }
            )
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422
