"""Pydantic models for image upload request/response."""

import base64
from typing import Any

from aws_lambda_powertools import Logger
from core.utils.constants import MAX_FILE_SIZE, USER_ID_PATTERN
from pydantic import BaseModel, ConfigDict, Field, field_validator

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
            tags = [t.strip() for t in value.split(",") if t.strip()]
        elif isinstance(value, list):
            tags = [str(t).strip() for t in value if str(t).strip()]
        else:
            raise ValueError("tags must be a string or list of strings")

        if len(tags) > 10:
            logger.error("Tag validation error: Maximum 10 tags allowed")
            raise ValueError("Maximum 10 tags allowed")

        return tags

    @field_validator("file")
    @classmethod
    def validate_file_size(cls, value: str) -> str:
        """Validate base64 file size (50MB max)."""
        try:
            file_data = base64.b64decode(value, validate=True)
            if len(file_data) > MAX_FILE_SIZE:
                logger.error("File size validation error: File size exceeds limit")
                raise ValueError(
                    f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
                )
            return value
        except Exception as e:
            logger.error(
                f"File validation error: Invalid base64 encoded file - {str(e)}"
            )
            raise ValueError(f"Invalid base64 encoded file: {str(e)}") from e

    @field_validator("image_name")
    @classmethod
    def validate_image_name(cls, value: str) -> str:
        if "." not in value:
            raise ValueError("image_name must include a file extension")
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
