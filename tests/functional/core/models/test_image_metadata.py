"""Unit tests for ImageMetadata and ListImagesResponse models."""

from pydantic import ValidationError
import pytest

from core.models.image import ImageMetadata, ListImagesResponse
from core.models.pagination import PaginationInfo


class TestImageMetadata:
    def test_create_image_metadata_success(self) -> None:
        metadata = ImageMetadata(
            image_id="img_1",
            user_id="john",
            image_name="photo.jpg",
            description="Test image",
            tags=["test", "sample"],
            created_at="2024-01-01T10:00:00Z",
            updated_at=None,
            s3_key="images/john/img_1.jpg",
            file_size=123,
            mime_type="image/jpeg",
        )

        assert metadata.image_id == "img_1"
        assert metadata.user_id == "john"
        assert metadata.image_name == "photo.jpg"
        assert metadata.description == "Test image"
        assert metadata.tags == ["test", "sample"]
        assert metadata.updated_at is None
        assert metadata.file_size == 123
        assert metadata.mime_type == "image/jpeg"

    def test_optional_fields_can_be_none(self) -> None:
        metadata = ImageMetadata(
            image_id="img_2",
            user_id="alice",
            image_name="image.png",
            created_at="2024-01-02T10:00:00Z",
            s3_key="images/alice/img_2.png",
            file_size=456,
            mime_type="image/png",
        )

        assert metadata.description is None
        assert metadata.tags is None
        assert metadata.updated_at is None

    def test_invalid_file_size_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            ImageMetadata(
                image_id="img_bad",
                user_id="john",
                image_name="bad.jpg",
                created_at="2024-01-01T10:00:00Z",
                s3_key="images/john/bad.jpg",
                file_size="123",
                mime_type="image/jpeg",
            )

    def test_invalid_tags_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            ImageMetadata(
                image_id="img_bad",
                user_id="john",
                image_name="bad.jpg",
                created_at="2024-01-01T10:00:00Z",
                s3_key="images/john/bad.jpg",
                file_size=100,
                mime_type="image/jpeg",
                tags="not-a-list",
            )


class TestListImagesResponse:
    def test_create_list_images_response_success(self) -> None:
        images = [
            ImageMetadata(
                image_id="img_1",
                user_id="john",
                image_name="photo.jpg",
                created_at="2024-01-01T10:00:00Z",
                s3_key="images/john/img_1.jpg",
                file_size=100,
                mime_type="image/jpeg",
            )
        ]

        pagination = PaginationInfo(
            limit=10,
            offset=0,
            has_more=False,
        )

        response = ListImagesResponse(
            images=images,
            total_count=1,
            returned_count=1,
            filter_applied=None,
            pagination=pagination,
        )

        assert response.total_count == 1
        assert response.returned_count == 1
        assert response.filter_applied is None
        assert response.pagination.limit == 10
        assert len(response.images) == 1
        assert response.images[0].image_id == "img_1"

    def test_list_images_response_invalid_images_type_raises(self) -> None:
        pagination = PaginationInfo(limit=10, offset=0, has_more=False)

        with pytest.raises(ValidationError):
            ListImagesResponse(
                images="not-a-list",
                total_count=1,
                returned_count=1,
                pagination=pagination,
            )

    def test_list_images_response_invalid_pagination_raises(self) -> None:
        with pytest.raises(ValidationError):
            ListImagesResponse(
                images=[],
                total_count=0,
                returned_count=0,
                pagination="invalid",
            )
