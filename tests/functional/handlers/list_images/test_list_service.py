import pytest

from core.models.errors import FilterError, MetadataOperationFailedError
from handlers.list_images.service import ListService


class TestListService:
    def test_list_all_images_for_user(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, total, has_more = service.list_images(
            user_id="john",
            name_contains=None,
            start_date=None,
            end_date=None,
            offset=0,
            limit=10,
            sort_by=None,
            sort_order=None,
        )

        assert total == 2
        assert len(items) == 2
        assert has_more is False
        assert {item["user_id"] for item in items} == {"john"}

    def test_list_with_name_filter(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, total, has_more = service.list_images(
            user_id="john",
            name_contains="sunset",
            start_date=None,
            end_date=None,
            offset=0,
            limit=10,
            sort_by=None,
            sort_order=None,
        )

        assert total == 1
        assert has_more is False
        assert items[0]["image_name"] == "sunset.jpg"

    def test_list_with_start_date_filter(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, total, _ = service.list_images(
            user_id="john",
            name_contains=None,
            start_date="2024-01-04T00:00:00Z",
            end_date=None,
            offset=0,
            limit=10,
            sort_by=None,
            sort_order=None,
        )

        assert total == 1
        assert items[0]["image_id"] == "img_4"

    def test_list_with_date_range_filter(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, total, _ = service.list_images(
            user_id="john",
            name_contains=None,
            start_date="2024-01-02T00:00:00+00:00",
            end_date="2024-01-04T23:59:59.999999+00:00",
            offset=0,
            limit=10,
            sort_by=None,
            sort_order=None,
        )

        assert total == 2
        assert {item["image_id"] for item in items} == {"img_2", "img_4"}

    def test_list_sorted_by_created_at_desc(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, _, _ = service.list_images(
            user_id="john",
            name_contains=None,
            start_date=None,
            end_date=None,
            offset=0,
            limit=10,
            sort_by="created_at",
            sort_order="desc",
        )

        assert [item["image_id"] for item in items] == ["img_4", "img_2"]

    def test_list_sorted_by_image_name_asc(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, _, _ = service.list_images(
            user_id="john",
            name_contains=None,
            start_date=None,
            end_date=None,
            offset=0,
            limit=10,
            sort_by="image_name",
            sort_order="asc",
        )

        assert [item["image_name"] for item in items] == [
            "b.png",
            "sunset.jpg",
        ]

    def test_list_with_pagination_has_more(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, total, has_more = service.list_images(
            user_id="john",
            name_contains=None,
            start_date=None,
            end_date=None,
            offset=0,
            limit=1,
            sort_by=None,
            sort_order=None,
        )

        assert len(items) == 1
        assert total == 1
        assert has_more is False

    def test_list_offset_beyond_range(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, total, has_more = service.list_images(
            user_id="john",
            name_contains=None,
            start_date=None,
            end_date=None,
            offset=10,
            limit=5,
            sort_by=None,
            sort_order=None,
        )

        assert items == []
        assert total == 2
        assert has_more is False

    def test_user_isolation(
        self,
        dynamodb_with_multiple_items,
    ) -> None:
        service = ListService()

        items, total, _ = service.list_images(
            user_id="alice",
            name_contains=None,
            start_date=None,
            end_date=None,
            offset=0,
            limit=10,
            sort_by=None,
            sort_order=None,
        )

        assert total == 1
        assert items[0]["user_id"] == "alice"

    def test_invalid_limit_raises_filter_error(self) -> None:
        service = ListService()

        with pytest.raises(FilterError):
            service.list_images(
                user_id="john",
                name_contains=None,
                start_date=None,
                end_date=None,
                offset=0,
                limit=0,
                sort_by=None,
                sort_order=None,
            )

    def test_metadata_failure_translated_to_domain_error(
        self,
        monkeypatch,
    ) -> None:
        service = ListService()

        monkeypatch.setattr(
            service.metadata,
            "list_user_images",
            lambda **_: (_ for _ in ()).throw(Exception("boom")),
        )

        with pytest.raises(MetadataOperationFailedError):
            service.list_images(
                user_id="john",
                name_contains=None,
                start_date=None,
                end_date=None,
                offset=0,
                limit=10,
                sort_by=None,
                sort_order=None,
            )
