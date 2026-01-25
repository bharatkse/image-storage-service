"""Shared image metadata model."""

from core.models.pagination import PaginationInfo
from pydantic import BaseModel, StrictInt, StrictStr


class ImageMetadata(BaseModel):
    """Image metadata for storage in DynamoDB."""

    image_id: StrictStr
    user_id: StrictStr
    image_name: StrictStr
    description: StrictStr | None = None
    tags: list[StrictStr] | None = None
    created_at: StrictStr
    updated_at: StrictStr | None = None
    s3_key: StrictStr
    file_size: StrictInt
    mime_type: StrictStr
    file_hash: StrictStr | None = None


class ListImagesResponse(BaseModel):
    """Response model for list images."""

    images: list[ImageMetadata]
    total_count: StrictInt
    returned_count: StrictInt
    filter_applied: StrictStr | None = None
    pagination: PaginationInfo
