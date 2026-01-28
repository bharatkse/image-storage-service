"""Shared image metadata model."""

from pydantic import BaseModel, Field, StrictInt, StrictStr

from core.models.pagination import PaginationInfo


class ImageMetadata(BaseModel):
    """Image metadata returned by the Image Storage API."""

    image_id: StrictStr = Field(..., description="Unique image identifier")
    user_id: StrictStr = Field(..., description="Owner user identifier")
    image_name: StrictStr = Field(..., description="Original image file name")

    description: StrictStr | None = Field(None, description="Optional image description")
    tags: list[StrictStr] | None = Field(None, description="Optional list of image tags")

    created_at: StrictStr = Field(..., description="ISO-8601 creation timestamp (UTC)")
    updated_at: StrictStr | None = Field(None, description="ISO-8601 last update timestamp (UTC)")

    s3_key: StrictStr = Field(..., description="S3 object key where the image is stored")
    file_size: StrictInt = Field(..., description="Image size in bytes")
    mime_type: StrictStr = Field(..., description="MIME type of the image (e.g. image/jpeg)")

    file_hash: StrictStr | None = None


class ListImagesResponse(BaseModel):
    """Paginated response for listing images."""

    images: list[ImageMetadata] = Field(..., description="List of image metadata objects")
    total_count: StrictInt = Field(..., description="Total number of images matching the query")
    returned_count: StrictInt = Field(..., description="Number of images returned in this response")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")
