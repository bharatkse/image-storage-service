"""Unit tests for PaginationInfo model."""

from pydantic import ValidationError
import pytest

from core.models.pagination import PaginationInfo


class TestPaginationInfo:
    def test_create_pagination_info_success(self) -> None:
        pagination = PaginationInfo(
            limit=10,
            offset=0,
            has_more=True,
        )

        assert pagination.limit == 10
        assert pagination.offset == 0
        assert pagination.has_more is True

    def test_pagination_info_zero_limit(self) -> None:
        pagination = PaginationInfo(
            limit=0,
            offset=0,
            has_more=False,
        )

        assert pagination.limit == 0
        assert pagination.offset == 0
        assert pagination.has_more is False

    def test_pagination_info_negative_offset_allowed(self) -> None:
        pagination = PaginationInfo(
            limit=10,
            offset=-1,
            has_more=False,
        )

        assert pagination.offset == -1

    def test_invalid_limit_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            PaginationInfo(
                limit="10",
                offset=0,
                has_more=False,
            )

    def test_invalid_offset_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            PaginationInfo(
                limit=10,
                offset="0",
                has_more=False,
            )

    def test_invalid_has_more_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            PaginationInfo(
                limit=10,
                offset=0,
                has_more="true",
            )
