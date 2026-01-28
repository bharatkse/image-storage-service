"""Global constants used throughout the application.

This module centralizes all magic numbers, string literals, and configuration
values that are used across multiple modules. Using constants prevents hardcoding
values and makes it easy to change them globally.
"""

from typing import Final

# ============================================================================
# Error Codes
# ============================================================================


# Validation Errors
ERROR_CODE_VALIDATION_FAILED = "VALIDATION_FAILED"
ERROR_CODE_INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
ERROR_CODE_INVALID_FILTER = "INVALID_FILTER"
ERROR_CODE_UNSUPPORTED_MIME_TYPE = "UNSUPPORTED_MIME_TYPE"
ERROR_CODE_FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"

# Not Found Errors
ERROR_CODE_RESOURCE_NOT_FOUND = "NOT_FOUND"
ERROR_CODE_IMAGE_NOT_FOUND = "IMAGE_NOT_FOUND"

# Storage Errors
ERROR_CODE_S3 = "S3_ERROR"
ERROR_CODE_IMAGE_UPLOAD_FAILED = "IMAGE_UPLOAD_FAILED"
ERROR_CODE_IMAGE_DOWNLOAD_FAILED = "IMAGE_DOWNLOAD_FAILED"
ERROR_CODE_IMAGE_DELETE_FAILED = "IMAGE_DELETE_FAILED"
ERROR_CODE_IMAGE_DUPLICATE_IMAGE = "DUPLICATE_IMAGE_ERROR"
ERROR_CODE_IMAGE_PRESIGNED_URL_FAILED = "PRESIGNED_URL_FAILED"

# Metadata / DynamoDB Errors
ERROR_CODE_DYNAMODB = "DYNAMODB_ERROR"
ERROR_CODE_METADATA_OPERATION_FAILED = "METADATA_OPERATION_FAILED"
ERROR_CODE_METADATA_CREATE_FAILED = "METADATA_CREATE_FAILED"
ERROR_CODE_METADATA_FETCH_FAILED = "METADATA_FETCH_FAILED"
ERROR_CODE_METADATA_DELETE_FAILED = "METADATA_DELETE_FAILED"
ERROR_CODE_METADATA_LIST_FAILED = "METADATA_LIST_FAILED"
ERROR_CODE_METADATA_DUPLICATE_CHECK_FAILED = "METADATA_DUPLICATE_CHECK_FAILED"
ERROR_CODE_METADATA_INVALID_FORMAT = "METADATA_INVALID_FORMAT"
ERROR_CODE_METADATA_INVALID_STATE = "METADATA_INVALID_STATE"

# Processing / Filtering Errors
ERROR_CODE_FILTER_FAILED = "FILTER_FAILED"

# Internal / Unexpected
ERROR_CODE_INTERNAL_ERROR = "INTERNAL_ERROR"


# ============================================================================
# File Upload Constraints
# ============================================================================

MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB in bytes


MIME_TYPE_EXTENSION_MAP: Final[dict[str, tuple[str, ...]]] = {
    "image/jpeg": ("jpg", "jpeg"),
    "image/png": ("png",),
    "image/gif": ("gif",),
    "image/webp": ("webp",),
    "image/svg+xml": ("svg",),
}

ALLOWED_MIME_TYPES: Final[frozenset[str]] = frozenset(MIME_TYPE_EXTENSION_MAP.keys())

ALLOWED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    ext for extensions in MIME_TYPE_EXTENSION_MAP.values() for ext in extensions
)


# ============================================================================
# Image Metadata Constraints
# ============================================================================

USER_ID_PATTERN = r"^[a-zA-Z0-9_-]+$"
MAX_TAGS = 10
TAG_MAX_LENGTH = 50

# ============================================================================
# Pagination Constraints
# ============================================================================

DEFAULT_LIMIT = 20
MIN_LIMIT = 1
MAX_LIMIT = 100
DEFAULT_OFFSET = 0

# ============================================================================
# Filter Constraints
# ============================================================================

ALLOWED_SORT_FIELDS = {"created_at", "image_name"}
ALLOWED_SORT_ORDERS = {"asc", "desc"}

# ============================================================================
# Date / Time Formats
# ============================================================================

DATE_FORMAT = "%Y-%m-%d"
API_DATE_FORMAT = "YYYY-MM-DD"

# ============================================================================
# API Gateway Configuration
# ============================================================================

CORS_ORIGIN = "*"
CORS_METHODS = "GET,POST,PUT,DELETE,OPTIONS"
CORS_HEADERS = "Content-Type,Authorization,X-Api-Key"
EXPOSE_HEADERS = "Content-Type,Content-Length,X-Image-Metadata"
DEFAULT_CONTENT_TYPE = "application/json"
BINARY_CONTENT_TYPE_HEADER = "Content-Type"

# ============================================================================
# Environment Variable Names
# ============================================================================

ENV_AWS_ENDPOINT_URL = "AWS_ENDPOINT_URL"
ENV_IMAGE_S3_BUCKET_NAME = "IMAGE_S3_BUCKET_NAME"
ENV_IMAGE_METADATA_TABLE_NAME = "IMAGE_METADATA_TABLE_NAME"
ENV_ENVIRONMENT = "ENVIRONMENT"
ENV_AWS_REGION = "us-east-1"
ENV_APP_RUNTIME = "APP_RUNTIME"
LOCALSTACK_URL = "http://localstack"
LOCALHOST_URL = "http://localhost"

# ============================================================================
# Helper Functions
# ============================================================================


def get_max_file_size_mb() -> int:
    """Get maximum file size in megabytes."""
    return MAX_FILE_SIZE // (1024 * 1024)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted file size string
    """
    size: float = float(size_bytes)

    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} TB"
