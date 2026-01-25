"""Unit tests for InMemoryImageFilter."""

import pytest
from core.filters.in_memory_image_filter import InMemoryImageFilter


class TestInMemoryImageFilter:
    """Tests for in-memory image filtering and pagination."""

    def test_filter_by_name_none_returns_all(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()
        result = service.filter_by_name_contains(items, name_contains=None)

        assert result == items

    def test_filter_by_name_empty_string_returns_all(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()
        result = service.filter_by_name_contains(items, name_contains="")

        assert result == items

    def test_filter_by_name_contains_matches_case_insensitive(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()
        result = service.filter_by_name_contains(items, name_contains="SunSeT")

        assert len(result) == 1
        assert result[0]["image_name"] == "sunset.jpg"

    def test_filter_by_name_no_matches_returns_empty(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()
        result = service.filter_by_name_contains(items, name_contains="does-not-exist")

        assert result == []

    def test_paginate_first_page(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()
        page, total, has_more = service.paginate(
            items,
            offset=0,
            limit=2,
        )

        assert total == len(items)
        assert len(page) == 2
        assert has_more is True

    def test_paginate_middle_page(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()
        page, total, has_more = service.paginate(
            items,
            offset=2,
            limit=2,
        )

        assert total == len(items)
        assert len(page) == 1
        assert has_more is False

    def test_paginate_offset_beyond_range_returns_empty(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()
        page, total, has_more = service.paginate(
            items,
            offset=100,
            limit=10,
        )

        assert page == []
        assert total == len(items)
        assert has_more is False

    def test_paginate_invalid_offset_raises_value_error(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()

        with pytest.raises(ValueError):
            service.paginate(items, offset=-1, limit=10)

    def test_paginate_invalid_limit_raises_value_error(
        self,
        dynamodb_table,
        dynamodb_put_multiple_items,
        multiple_image_metadata_items,
    ) -> None:
        dynamodb_put_multiple_items(multiple_image_metadata_items)
        items = dynamodb_table.scan()["Items"]

        service = InMemoryImageFilter()

        with pytest.raises(ValueError):
            service.paginate(items, offset=0, limit=0)
