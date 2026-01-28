"""
Unit tests for core.models.errors
"""

from core.models.errors import (
    DuplicateImageError,
    DynamoDBError,
    FileSizeError,
    FilterError,
    ImageServiceError,
    MetadataOperationFailedError,
    MIMETypeError,
    NotFoundError,
    S3Error,
    ValidationError,
)


class TestImageServiceError:
    def test_base_error(self) -> None:
        err = ImageServiceError(
            message="Something went wrong",
            error_code="TEST_ERROR",
            details={"foo": "bar"},
        )

        assert isinstance(err, ImageServiceError)
        assert err.message == "Something went wrong"
        assert err.error_code == "TEST_ERROR"
        assert err.details == {"foo": "bar"}


class TestValidationError:
    def test_validation_error_defaults(self) -> None:
        err = ValidationError(message="Invalid input")

        assert err.error_code == "VALIDATION_FAILED"
        assert err.details == {}
        assert str(err) == "Invalid input"

    def test_validation_error_with_details(self) -> None:
        err = ValidationError(
            message="Invalid value",
            details={"field": "image_id"},
        )

        assert err.details == {"field": "image_id"}


class TestNotFoundError:
    def test_not_found_error(self) -> None:
        err = NotFoundError(
            message="Image not found",
            details={"image_id": "img_123"},
        )

        assert err.error_code == "NOT_FOUND"
        assert err.details == {"image_id": "img_123"}


class TestDuplicateImageError:
    def test_duplicate_image_error(self) -> None:
        err = DuplicateImageError(
            message="Duplicate image detected",
            details={"file_hash": "abc123"},
        )

        assert err.error_code == "DUPLICATE_IMAGE_ERROR"
        assert err.details["file_hash"] == "abc123"


class TestMetadataOperationFailedError:
    def test_metadata_operation_failed_error(self) -> None:
        err = MetadataOperationFailedError(
            message="Failed to save metadata",
            details={"image_id": "img_1"},
        )

        assert err.error_code == "METADATA_OPERATION_FAILED"
        assert err.details["image_id"] == "img_1"


class TestS3Error:
    def test_s3_error(self) -> None:
        err = S3Error(
            message="S3 operation failed",
            details={"operation": "upload"},
        )

        assert err.error_code == "S3_ERROR"
        assert err.details == {"operation": "upload"}


class TestDynamoDBError:
    def test_dynamodb_error(self) -> None:
        err = DynamoDBError(
            message="DynamoDB query failed",
            details={"operation": "query"},
        )

        assert err.error_code == "DYNAMODB_ERROR"
        assert err.details == {"operation": "query"}


class TestFilterError:
    def test_filter_error(self) -> None:
        err = FilterError(
            message="Invalid filter",
            details={"filter": "date"},
        )

        assert err.error_code == "INVALID_FILTER"
        assert err.details == {"filter": "date"}


class TestMIMETypeError:
    def test_mime_type_error(self) -> None:
        err = MIMETypeError(
            message="Unsupported MIME type",
            details={"mime_type": "application/xml"},
        )

        assert err.error_code == "UNSUPPORTED_MIME_TYPE"
        assert err.details["mime_type"] == "application/xml"


class TestFileSizeError:
    def test_file_size_error(self) -> None:
        err = FileSizeError(
            message="File size exceeded",
            details={"size": 10_000, "max_size": 5_000},
        )

        assert err.error_code == "FILE_SIZE_EXCEEDED"
        assert err.details["size"] == 10_000
        assert err.details["max_size"] == 5_000
