"""Pagination model."""

from pydantic import BaseModel, Field, StrictBool, StrictInt


class PaginationInfo(BaseModel):
    """Pagination metadata for list responses."""

    limit: StrictInt = Field(..., description="Maximum number of items requested")
    offset: StrictInt = Field(..., description="Current offset in the result set")
    has_more: StrictBool = Field(..., description="Whether more items are available after this page")
    next_offset: StrictInt | None = Field(
        None,
        description="Offset to use for the next page, if available",
    )
