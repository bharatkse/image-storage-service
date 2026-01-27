"""
Unit tests for ListImagesRequest
"""

import pytest
from pydantic import ValidationError

from core.utils.constants import DEFAULT_LIMIT, DEFAULT_OFFSET
from handlers.list_image.models import ListImagesRequest


class TestListImagesRequest:
    def test_valid_minimal_request(self) -> None:
        req = ListImagesRequest(user_id="john_doe")

        assert req.user_id == "john_doe"
        assert req.limit == DEFAULT_LIMIT
        assert req.offset == DEFAULT_OFFSET
        assert req.sort_by == "created_at"
        assert req.sort_order == "desc"
        assert req.name_contains is None
        assert req.start_date is None
        assert req.end_date is None

    def test_name_contains_filter(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            name_contains="sunset",
        )

        assert req.name_contains == "sunset"

    def test_name_contains_whitespace_trimmed(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            name_contains="  sunset  ",
        )

        assert req.name_contains == "sunset"

    def test_valid_start_date_normalization(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            start_date="2024-01-15",
        )

        assert req.start_date == "2024-01-15T00:00:00+00:00"

    def test_valid_end_date_normalization(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            end_date="2024-01-15",
        )

        assert req.end_date == "2024-01-15T23:59:59.999999+00:00"

    def test_valid_date_range(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert req.start_date < req.end_date

    def test_invalid_date_format_start_date(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                start_date="15-01-2024",
            )

    def test_invalid_date_format_end_date(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                end_date="2024/01/15",
            )

    def test_start_date_after_end_date_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                start_date="2024-02-01",
                end_date="2024-01-01",
            )

    def test_limit_lower_bound(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            limit=1,
        )

        assert req.limit == 1

    def test_limit_upper_bound(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            limit=100,
        )

        assert req.limit == 100

    def test_limit_above_max_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                limit=101,
            )

    def test_limit_below_min_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                limit=0,
            )

    def test_offset_zero_valid(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            offset=0,
        )

        assert req.offset == 0

    def test_negative_offset_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                offset=-1,
            )

    def test_sorting_explicit_valid(self) -> None:
        req = ListImagesRequest(
            user_id="john_doe",
            sort_by="image_name",
            sort_order="asc",
        )

        assert req.sort_by == "image_name"
        assert req.sort_order == "asc"

    def test_invalid_sort_by_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                sort_by="size",
            )

    def test_invalid_sort_order_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(
                user_id="john_doe",
                sort_order="up",
            )

    def test_user_id_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(user_id="ab")

    def test_user_id_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesRequest(user_id="x" * 51)
