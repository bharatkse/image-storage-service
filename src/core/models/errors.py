"""Custom exception classes for the image service."""

from typing import Any

from core.utils.constants import (
    ERROR_CODE_DYNAMODB,
    ERROR_CODE_FILE_SIZE_EXCEEDED,
    ERROR_CODE_IMAGE_DUPLICATE_IMAGE,
    ERROR_CODE_INVALID_FILTER,
    ERROR_CODE_METADATA_OPERATION_FAILED,
    ERROR_CODE_RESOURCE_NOT_FOUND,
    ERROR_CODE_S3,
    ERROR_CODE_UNSUPPORTED_MIME_TYPE,
    ERROR_CODE_VALIDATION_FAILED,
)


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
        error_code: str = ERROR_CODE_VALIDATION_FAILED,
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
        error_code: str = ERROR_CODE_RESOURCE_NOT_FOUND,
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
        error_code: str = ERROR_CODE_IMAGE_DUPLICATE_IMAGE,
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
        error_code: str = ERROR_CODE_METADATA_OPERATION_FAILED,
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
        error_code: str = ERROR_CODE_S3,
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
        error_code: str = ERROR_CODE_DYNAMODB,
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
        error_code: str = ERROR_CODE_INVALID_FILTER,
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
        error_code: str = ERROR_CODE_UNSUPPORTED_MIME_TYPE,
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
        error_code: str = ERROR_CODE_FILE_SIZE_EXCEEDED,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
        )
