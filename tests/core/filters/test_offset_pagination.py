from typing import Any

from core.filters.offset_pagination import OffsetPagination
from core.utils.constants import MAX_LIMIT, MIN_LIMIT


class TestOffsetPagination:
    def test_paginate_first_page(self) -> None:
        items: list[dict[str, Any]] = [{"id": i} for i in range(50)]

        page, total, has_more = OffsetPagination.paginate(
            items,
            offset=0,
            limit=20,
        )

        assert len(page) == 20
        assert total == 50
        assert has_more is True

    def test_paginate_last_page(self) -> None:
        items: list[dict[str, Any]] = [{"id": i} for i in range(50)]

        page, total, has_more = OffsetPagination.paginate(
            items,
            offset=40,
            limit=20,
        )

        assert len(page) == 10
        assert total == 50
        assert has_more is False

    def test_paginate_offset_beyond_range(self) -> None:
        items: list[dict[str, Any]] = [{"id": i} for i in range(10)]

        page, total, has_more = OffsetPagination.paginate(
            items,
            offset=100,
            limit=10,
        )

        assert page == []
        assert total == 10
        assert has_more is False

    def test_validate_valid_params(self) -> None:
        is_valid, error = OffsetPagination.validate(
            limit=MIN_LIMIT,
            offset=0,
        )

        assert is_valid is True
        assert error == ""

    def test_validate_limit_too_small(self) -> None:
        is_valid, error = OffsetPagination.validate(
            limit=MIN_LIMIT - 1,
            offset=0,
        )

        assert is_valid is False
        assert "at least" in error

    def test_validate_limit_too_large(self) -> None:
        is_valid, error = OffsetPagination.validate(
            limit=MAX_LIMIT + 1,
            offset=0,
        )

        assert is_valid is False
        assert "must not exceed" in error

    def test_validate_negative_offset(self) -> None:
        is_valid, error = OffsetPagination.validate(
            limit=10,
            offset=-1,
        )

        assert is_valid is False
        assert error == "Offset must be zero or a positive integer"

    def test_get_page_info(self) -> None:
        info = OffsetPagination.get_page_info(
            offset=20,
            limit=10,
            total_count=95,
        )

        assert info["offset"] == 20
        assert info["limit"] == 10
        assert info["total_count"] == 95
        assert info["has_more"] is True
        assert info["current_page"] == 3
        assert info["total_pages"] == 10
