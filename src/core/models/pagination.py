"""Pagination model."""

from pydantic import BaseModel, StrictBool, StrictInt


class PaginationInfo(BaseModel):
    """Pagination information."""

    limit: StrictInt
    offset: StrictInt
    has_more: StrictBool
