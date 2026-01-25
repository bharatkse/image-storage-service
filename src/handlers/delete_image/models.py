"""Pydantic models for delete image request/response."""

from pydantic import BaseModel, ConfigDict, Field


class DeleteImageRequest(BaseModel):
    """Validation model for delete image request."""

    model_config = ConfigDict(str_strip_whitespace=True)
    image_id: str = Field(
        ...,
        min_length=1,
        description="Image ID to delete",
    )


class DeleteImageResponse(BaseModel):
    """Response model for successful image deletion."""

    image_id: str = Field(..., description="Deleted image ID")
    message: str = Field(..., description="Success message")
    deleted_at: str = Field(..., description="Deletion timestamp")
    s3_key: str = Field(..., description="S3 object key that was deleted")
