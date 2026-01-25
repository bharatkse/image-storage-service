"""Global constants used throughout the application.

This module centralizes all magic numbers, string literals, and configuration
values that are used across multiple modules. Using constants prevents hardcoding
values and makes it easy to change them globally.
"""


# ============================================================================
# Error Codes
# ============================================================================

ERROR_CODE_VALIDATION = "VALIDATION_ERROR"
ERROR_CODE_NOT_FOUND = "IMAGE_NOT_FOUND"
ERROR_CODE_S3 = "S3_ERROR"
ERROR_CODE_DYNAMODB = "DYNAMODB_ERROR"
ERROR_CODE_FILTER = "FILTER_ERROR"
ERROR_CODE_MIME_TYPE = "UNSUPPORTED_MIME_TYPE"
ERROR_CODE_FILE_SIZE = "FILE_SIZE_EXCEEDED"
ERROR_CODE_INTERNAL = "INTERNAL_SERVER_ERROR"

# ============================================================================
# Error Messages
# ============================================================================

ERROR_MSG_INVALID_REQUEST = "Invalid request parameters"
ERROR_MSG_IMAGE_NOT_FOUND = "Image not found"
ERROR_MSG_S3_UPLOAD_FAILED = "Failed to upload image to S3"
ERROR_MSG_S3_DOWNLOAD_FAILED = "Failed to download image from S3"
ERROR_MSG_S3_DELETE_FAILED = "Failed to delete image from S3"
ERROR_MSG_DB_SAVE_FAILED = "Failed to save metadata to DynamoDB"
ERROR_MSG_DB_GET_FAILED = "Failed to retrieve metadata from DynamoDB"
ERROR_MSG_DB_DELETE_FAILED = "Failed to delete metadata from DynamoDB"
ERROR_MSG_DB_QUERY_FAILED = "Failed to query images from DynamoDB"
ERROR_MSG_INVALID_MIME_TYPE = "Unsupported file type"
ERROR_MSG_FILE_TOO_LARGE = "File size exceeds maximum limit"
ERROR_MSG_INVALID_DATE = "Invalid date format"
ERROR_MSG_INVALID_FILTER = "Invalid filter parameters"


# ============================================================================
# File Upload Constraints
# ============================================================================

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB in bytes

ALLOWED_MIME_TYPES: list[str] = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
]

MIME_TYPE_EXTENSION_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
}

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

FILTER_TYPE_NAME = "name"
FILTER_TYPE_DATE = "date"

VALID_FILTER_TYPES = [FILTER_TYPE_NAME, FILTER_TYPE_DATE]
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
CORS_HEADERS = "Content-Type,X-Api-Key,Authorization"

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
