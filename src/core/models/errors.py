"""Custom exception classes for the image service."""

from typing import Any


class ImageServiceError(Exception):
    """
    Base exception for all image service errors.

    All custom errors must inherit from this class.
    Callers must explicitly provide a message and error code.
    Optional contextual information can be supplied via `details`.
    """

    message: str
    error_code: str
    details: dict[str, Any]

    def __init__(
        self,
        *,
        message: str,
        error_code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}

        super().__init__(self.message)


class ValidationError(ImageServiceError):
    """Raised when request validation fails."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class NotFoundError(ImageServiceError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class DuplicateImageError(ImageServiceError):
    """Raised when a duplicate image is detected."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "DUPLICATE_IMAGE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class MetadataOperationFailedError(ImageServiceError):
    """Raised when an image metadata operation fails."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "METADATA_OPERATION_FAILED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class S3Error(ImageServiceError):
    """Raised when an image storage operation fails."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "S3_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class DynamoDBError(ImageServiceError):
    """Raised when a DynamoDB operation fails."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "DYNAMODB_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class ImageUploadFailedError(ImageServiceError):
    """Raised when image upload fails."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "IMAGE_UPLOAD_FAILED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class ImageDownloadFailedError(ImageServiceError):
    """Raised when image download fails."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "IMAGE_DOWNLOAD_FAILED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class ImageDeletionFailedError(ImageServiceError):
    """Raised when image deletion fails."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "IMAGE_DELETION_FAILED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class FilterError(ImageServiceError):
    """Raised when filter parameters are invalid."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "FILTER_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class MIMETypeError(ImageServiceError):
    """Raised when an unsupported MIME type is provided."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "UNSUPPORTED_MIME_TYPE",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )


class FileSizeError(ImageServiceError):
    """Raised when file size exceeds the allowed limit."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "FILE_SIZE_EXCEEDED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )
