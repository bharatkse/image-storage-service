"""
Business logic for image listing and filtering.
"""

from typing import Any

from aws_lambda_powertools import Logger
from core.filters.in_memory_image_filter import InMemoryImageFilter
from core.infrastructure.aws.dynamodb_metadata import DynamoDBMetadata
from core.models.errors import FilterError, MetadataOperationFailedError

Metadata = dict[str, Any]

logger = Logger(UTC=True)


class ListService:
    """Application service responsible for listing user images.

    This service coordinates:
    - Fetching image metadata from DynamoDB
    - Applying optional in-memory refinement filters
    - Sorting and paginating results
    """

    def __init__(self) -> None:
        """Initialize list service with required dependencies."""
        self.metadata = DynamoDBMetadata()
        self.filters = InMemoryImageFilter()

    def list_images(
        self,
        *,
        user_id: str,
        name_contains: str | None,
        start_date: str | None,
        end_date: str | None,
        offset: int,
        limit: int,
        sort_by: str | None,
        sort_order: str | None,
    ) -> tuple[list[Metadata], int, bool]:
        """List images with filtering, sorting, and pagination."""

        if limit < 1 or limit > 100:
            raise FilterError(
                message="Limit must be between 1 and 100",
                details={"limit": limit},
            )

        try:
            # Step 1: Fetch from DynamoDB (date filtering only)
            items = self.metadata.list_user_images(
                user_id=user_id,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
            )

        except Exception as exc:
            logger.exception("Failed to fetch metadata")
            raise MetadataOperationFailedError(
                message="Unable to retrieve images",
                error_code="METADATA_LIST_FAILED",
                details={"user_id": user_id},
            ) from exc

        # Step 2: Apply in-memory name filtering only if requested
        if name_contains:
            items = self.filters.filter_by_name_contains(
                items,
                name_contains=name_contains,
            )

        # Step 3: Apply sorting only if explicitly requested
        if sort_by or sort_order:
            items = self._sort_items(
                items,
                sort_by=sort_by,
                sort_order=sort_order,
            )

        # Step 4: Apply pagination only when necessary
        if offset > 0 or limit:
            page_items, total, has_more = self.filters.paginate(
                items,
                offset=offset,
                limit=limit,
            )
        else:
            page_items = items
            total = len(items)
            has_more = False

        logger.info(
            "Images listed successfully",
            extra={"user_id": user_id, "count": len(page_items)},
        )

        return page_items, total, has_more

    @staticmethod
    def _sort_items(
        items: list[Metadata],
        *,
        sort_by: str | None,
        sort_order: str | None,
    ) -> list[Metadata]:
        """Sort images by the requested field."""
        field = sort_by or "created_at"
        reverse = (sort_order or "desc") == "desc"

        try:
            return sorted(
                items,
                key=lambda item: item.get(field) or "",
                reverse=reverse,
            )
        except Exception as exc:
            logger.exception("Sorting failed")
            raise FilterError(
                message="Invalid sort configuration",
                details={"sort_by": sort_by, "sort_order": sort_order},
            ) from exc
