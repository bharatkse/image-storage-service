"""
Offset-based pagination utilities.
"""

from typing import Any

from core.utils.constants import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    MAX_LIMIT,
    MIN_LIMIT,
)


class OffsetPagination:
    """
    Offset-based pagination helper.

    This class encapsulates all logic related to paginating a list of items
    using an offset and limit approach.

    Typical usage:
    1. Validate offset and limit parameters
    2. Apply pagination to a list of items
    3. Return paginated items along with metadata
    """

    @staticmethod
    def paginate(
        items: list[dict[str, Any]],
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> tuple[list[dict[str, Any]], int, bool]:
        """
        Paginate a list of items using offset and limit.

        This method slices the provided list and returns:
        - The current page of items
        - The total number of items before pagination
        - A boolean indicating whether more items exist after this page

        Args:
            items: Full list of items to paginate
            offset: Number of items to skip from the start
            limit: Maximum number of items to include in the page

        Returns:
            A tuple containing:
            - paginated_items: List of items for the current page
            - total_count: Total number of items before pagination
            - has_more: True if more items exist beyond this page

        Example:
            items = [1, 2, 3, 4, 5]
            offset = 0
            limit = 2

            → ([1, 2], 5, True)
        """
        total_count = len(items)
        paginated_items = items[offset : offset + limit]
        has_more = offset + limit < total_count

        return paginated_items, total_count, has_more

    @staticmethod
    def validate(limit: int, offset: int) -> tuple[bool, str]:
        """
        Validate pagination parameters.

        This method performs defensive validation to prevent invalid
        or abusive pagination requests.

        Validation rules:
        - limit must be within [MIN_LIMIT, MAX_LIMIT]
        - offset must be zero or positive

        Args:
            limit: Requested page size
            offset: Requested offset

        Returns:
            A tuple of:
            - is_valid: Whether parameters are valid
            - error_message: Human-readable error message if invalid

        Example:
            validate(limit=20, offset=0)
            → (True, "")
        """
        if limit < MIN_LIMIT:
            return False, f"Limit must be at least {MIN_LIMIT}"

        if limit > MAX_LIMIT:
            return False, f"Limit must not exceed {MAX_LIMIT}"

        if offset < 0:
            return False, "Offset must be zero or a positive integer"

        return True, ""

    @staticmethod
    def get_page_info(
        offset: int,
        limit: int,
        total_count: int,
    ) -> dict[str, Any]:
        """
        Generate pagination metadata for API responses.

        This helper method is useful when you want to expose pagination
        information to API consumers (e.g., current page, total pages).

        Args:
            offset: Current offset
            limit: Page size
            total_count: Total number of available items

        Returns:
            Dictionary containing pagination metadata:
            - offset
            - limit
            - total_count
            - has_more
            - current_page
            - total_pages

        Notes:
            - Page numbering starts at 1
            - total_pages is rounded up
        """
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
        current_page = (offset // limit) + 1 if limit > 0 else 1

        return {
            "offset": offset,
            "limit": limit,
            "total_count": total_count,
            "has_more": offset + limit < total_count,
            "current_page": current_page,
            "total_pages": total_pages,
        }
