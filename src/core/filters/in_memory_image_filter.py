"""
Image filtering service for list operations.

Provides a coordination layer that applies filtering and pagination
strategies to in-memory image metadata collections. This service does
not perform data access and is intended to operate on pre-fetched items.
"""

from typing import Any

from aws_lambda_powertools import Logger

from core.filters.name_contains_filter import NameContainsFilter
from core.filters.offset_pagination import OffsetPagination

ImageItem = dict[str, Any]
logger = Logger(UTC=True)


class InMemoryImageFilter:
    """
    Service responsible for filtering and paginating image metadata.

    This class orchestrates in-memory refinement strategies:
    - Name-based filtering (case-insensitive substring matching)
    - Offset-based pagination

    IMPORTANT:
    - Date-based filtering is intentionally NOT supported here.
    - Date filtering must be performed at the DynamoDB level.
    """

    def __init__(self) -> None:
        """Initialize filter components used for orchestration."""
        self._name_filter: NameContainsFilter = NameContainsFilter()
        self._pagination: OffsetPagination = OffsetPagination()

    def filter_by_name_contains(
        self,
        items: list[ImageItem],
        *,
        name_contains: str | None,
    ) -> list[ImageItem]:
        """
        Apply substring-based name filtering to image metadata.

        Args:
            items: List of image metadata dictionaries
            name_contains: Substring to match in image names

        Returns:
            Filtered list of image metadata
        """
        if not name_contains:
            return items

        result: list[ImageItem] = self._name_filter.apply(items, name_contains)
        return result

    def paginate(
        self,
        items: list[ImageItem],
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[ImageItem], int, bool]:
        """
        Apply offset-based pagination to a list of items.

        Args:
            items: List of filtered image metadata
            offset: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            A tuple of (paginated_items, total_count, has_more)

        Raises:
            ValueError: If pagination parameters are invalid
        """
        is_valid, error_message = self._pagination.validate(limit, offset)
        if not is_valid:
            logger.error(
                "Invalid pagination parameters",
                extra={
                    "limit": limit,
                    "offset": offset,
                    "error": error_message,
                },
            )
            raise ValueError(error_message)

        paginated_items, total_count, has_more = self._pagination.paginate(
            items, offset, limit
        )
        return paginated_items, total_count, has_more
