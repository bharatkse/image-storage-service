"""
Unit tests for core.models.errors
"""

from typing import cast

from core.models.errors import (
    DuplicateImageError,
    DynamoDBError,
    FileSizeError,
    FilterError,
    ImageDeletionFailedError,
    ImageDownloadFailedError,
    ImageServiceError,
    ImageUploadFailedError,
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
        typed = cast(ValidationError, err)

        assert typed.error_code == "VALIDATION_ERROR"
        assert typed.details == {}
        assert str(typed) == "Invalid input"

    def test_validation_error_with_details(self) -> None:
        err = ValidationError(
            message="Invalid value",
            details={"field": "image_id"},
        )
        typed = cast(ValidationError, err)

        assert typed.details == {"field": "image_id"}


class TestNotFoundError:
    def test_not_found_error(self) -> None:
        err = NotFoundError(
            message="Image not found",
            details={"image_id": "img_123"},
        )
        typed = cast(NotFoundError, err)

        assert typed.error_code == "NOT_FOUND"
        assert typed.details == {"image_id": "img_123"}


class TestDuplicateImageError:
    def test_duplicate_image_error(self) -> None:
        err = DuplicateImageError(
            message="Duplicate image detected",
            details={"file_hash": "abc123"},
        )
        typed = cast(DuplicateImageError, err)

        assert typed.error_code == "DUPLICATE_IMAGE_ERROR"
        assert typed.details["file_hash"] == "abc123"


class TestMetadataOperationFailedError:
    def test_metadata_operation_failed_error(self) -> None:
        err = MetadataOperationFailedError(
            message="Failed to save metadata",
            details={"image_id": "img_1"},
        )
        typed = cast(MetadataOperationFailedError, err)

        assert typed.error_code == "METADATA_OPERATION_FAILED"
        assert typed.details["image_id"] == "img_1"


class TestS3Error:
    def test_s3_error(self) -> None:
        err = S3Error(
            message="S3 operation failed",
            details={"operation": "upload"},
        )
        typed = cast(S3Error, err)

        assert typed.error_code == "S3_ERROR"
        assert typed.details == {"operation": "upload"}


class TestDynamoDBError:
    def test_dynamodb_error(self) -> None:
        err = DynamoDBError(
            message="DynamoDB query failed",
            details={"operation": "query"},
        )
        typed = cast(DynamoDBError, err)

        assert typed.error_code == "DYNAMODB_ERROR"
        assert typed.details == {"operation": "query"}


class TestImageStorageErrors:
    def test_image_upload_failed_error(self) -> None:
        err = ImageUploadFailedError(message="Upload failed")
        typed = cast(ImageUploadFailedError, err)

        assert typed.error_code == "IMAGE_UPLOAD_FAILED"

    def test_image_download_failed_error(self) -> None:
        err = ImageDownloadFailedError(message="Download failed")
        typed = cast(ImageDownloadFailedError, err)

        assert typed.error_code == "IMAGE_DOWNLOAD_FAILED"

    def test_image_deletion_failed_error(self) -> None:
        err = ImageDeletionFailedError(message="Delete failed")
        typed = cast(ImageDeletionFailedError, err)

        assert typed.error_code == "IMAGE_DELETION_FAILED"


class TestFilterError:
    def test_filter_error(self) -> None:
        err = FilterError(
            message="Invalid filter",
            details={"filter": "date"},
        )
        typed = cast(FilterError, err)

        assert typed.error_code == "FILTER_ERROR"
        assert typed.details == {"filter": "date"}


class TestMIMETypeError:
    def test_mime_type_error(self) -> None:
        err = MIMETypeError(
            message="Unsupported MIME type",
            details={"mime_type": "application/xml"},
        )
        typed = cast(MIMETypeError, err)

        assert typed.error_code == "UNSUPPORTED_MIME_TYPE"
        assert typed.details["mime_type"] == "application/xml"


class TestFileSizeError:
    def test_file_size_error(self) -> None:
        err = FileSizeError(
            message="File size exceeded",
            details={"size": 10_000, "max_size": 5_000},
        )
        typed = cast(FileSizeError, err)

        assert typed.error_code == "FILE_SIZE_EXCEEDED"
        assert typed.details["size"] == 10_000
        assert typed.details["max_size"] == 5_000
