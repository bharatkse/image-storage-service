"""Pydantic models for image upload request/response."""

import base64
from pathlib import Path
from typing import Any

from aws_lambda_powertools import Logger
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.utils.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, USER_ID_PATTERN

logger = Logger(UTC=True)


class ImageUploadRequest(BaseModel):
    """Validation model for image upload request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file: str = Field(..., description="Base64 encoded image file")
    user_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=USER_ID_PATTERN,
        description="User identifier (alphanumeric, underscore, hyphen)",
    )
    image_name: str = Field(
        ..., min_length=1, max_length=255, description="Image filename"
    )
    description: str | None = Field(
        None, max_length=1000, description="Image description"
    )
    tags: list[str] | None = Field(None, description="List of tags (max 10)")

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: Any) -> list[str] | None:
        """
        Normalize and validate tags.

        Accepts:
        - comma-separated string
        - list of strings

        Returns:
        - list[str] or None
        """
        if value is None:
            return None

        if isinstance(value, str):
            raw_tags = [t.strip() for t in value.split(",") if t.strip()]
        elif isinstance(value, list):
            raw_tags = [str(t).strip() for t in value if str(t).strip()]
        else:
            raise ValueError("tags must be a string or list of strings")

        # remove empty + deduplicate while preserving order
        tags: list[str] = list(dict.fromkeys(t for t in raw_tags if t))

        if len(tags) > 10:
            logger.error("Tag validation error: Maximum 10 tags allowed")
            raise ValueError("Maximum 10 tags allowed")

        return tags

    @field_validator("image_name")
    @classmethod
    def validate_image_name(cls, value: str) -> str:
        name = value.strip()
        suffix = Path(name).suffix.lower().lstrip(".")

        if not suffix:
            raise ValueError("Image name must have an extension")

        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid image extension '{suffix}'. "
                f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        return value

    @field_validator("file")
    @classmethod
    def validate_file(cls, value: str) -> str:
        """
        Validate base64 file:
        - must not be empty
        - must decode correctly
        - must have non-zero size
        - must not exceed MAX_FILE_SIZE
        """
        if not value or not value.strip():
            raise ValueError("file must not be empty")

        try:
            file_data = base64.b64decode(value, validate=True)
        except Exception as e:
            logger.error(f"File validation error: Invalid base64 - {e}")
            raise ValueError("Invalid base64 encoded file") from e

        if not file_data:
            logger.error("File validation error: Decoded file is empty")
            raise ValueError("Decoded file is empty")

        if len(file_data) > MAX_FILE_SIZE:
            logger.error("File size validation error: File size exceeds limit")
            raise ValueError(
                f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit"
            )

        return value


class ImageUploadResponse(BaseModel):
    """Response model for successful image upload."""

    image_id: str = Field(..., description="Unique image ID")
    user_id: str = Field(..., description="User ID")
    image_name: str = Field(..., description="Image name")
    description: str | None = Field(None, description="Image description")
    created_at: str = Field(..., description="Creation timestamp")
    s3_key: str = Field(..., description="S3 object key")
    message: str = Field(..., description="Success message")
