"""
Pydantic models for list images request and response.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from core.utils.constants import DEFAULT_LIMIT, DEFAULT_OFFSET


class ListImagesRequest(BaseModel):
    """
    Validation model for list images API.

    Supports two filters:
    - Date range (start_date, end_date) → DynamoDB-level
    - Image name substring (name_contains) → in-memory
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    # User identifier
    user_id: str = Field(..., min_length=3, max_length=50)

    # Filter 1: Name-based (in-memory filtering)
    name_contains: str | None = Field(
        None,
        description="Substring match on image name",
    )

    # Filter 2: Date-based (DynamoDB-level filtering)
    start_date: str | None = Field(
        None,
        description="Start date (YYYY-MM-DD) - normalized to beginning of day",
    )
    end_date: str | None = Field(
        None,
        description="End date (YYYY-MM-DD) - normalized to end of day",
    )

    # Pagination
    limit: int = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Results per page (1-100)",
    )
    offset: int = Field(
        default=DEFAULT_OFFSET,
        ge=0,
        description="Pagination offset",
    )

    # Sorting
    sort_by: Literal["created_at", "image_name"] = Field(
        default="created_at",
        description="Sort field",
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort order",
    )

    @field_validator("start_date")
    @classmethod
    def normalize_start_date(cls, value: str | None) -> str | None:
        """Normalize start_date to beginning of day (00:00:00 UTC).

        Input:  "2024-01-15"
        Output: "2024-01-15T00:00:00+00:00"

        This ensures we include all records from the start of the day.
        """
        if not value:
            return None

        try:
            # Parse date from YYYY-MM-DD format
            dt = datetime.fromisoformat(value)

            # Set to beginning of day (00:00:00 UTC)
            normalized = dt.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=timezone.utc,
            )

            return normalized.isoformat()
        except ValueError as exc:
            raise ValueError(
                f"Invalid date format. Expected YYYY-MM-DD, got '{value}'"
            ) from exc

    @field_validator("end_date")
    @classmethod
    def normalize_end_date(cls, value: str | None) -> str | None:
        """Normalize end_date to end of day (23:59:59.999999 UTC).

        Input:  "2024-01-15"
        Output: "2024-01-15T23:59:59.999999+00:00"

        This ensures we include all records from the end of the day.
        """
        if not value:
            return None

        try:
            # Parse date from YYYY-MM-DD format
            dt = datetime.fromisoformat(value)

            # Set to end of day (23:59:59.999999 UTC)
            normalized = dt.replace(
                hour=23,
                minute=59,
                second=59,
                microsecond=999999,
                tzinfo=timezone.utc,
            )

            return normalized.isoformat()
        except ValueError as exc:
            raise ValueError(
                f"Invalid date format. Expected YYYY-MM-DD, got '{value}'"
            ) from exc

    @model_validator(mode="after")
    def validate_date_range(self) -> "ListImagesRequest":
        """Ensure start_date is before or equal to end_date."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before or equal to end_date")
        return self
