"""Unit tests for DynamoDBMetadata repository."""

from collections.abc import Callable
from typing import Any

import pytest
from botocore.exceptions import ClientError
from core.infrastructure.aws.dynamodb_metadata import DynamoDBMetadata
from core.models.errors import (
    DuplicateImageError,
    FilterError,
    MetadataOperationFailedError,
)


class DummyAdapter:
    """Minimal DynamoDBAdapter stub."""

    put_item: Callable[..., Any]
    get_item: Callable[..., dict[str, Any]]
    delete_item: Callable[..., Any]
    query: Callable[..., dict[str, Any]]

    def __init__(self) -> None:
        self.put_item = lambda **_: None
        self.get_item = lambda **_: {}
        self.delete_item = lambda **_: None
        self.query = lambda **_: {"Items": []}


class TestDynamoDBMetadata:
    def test_create_metadata_success(self) -> None:
        repo = DynamoDBMetadata(DummyAdapter())
        repo.create_metadata(metadata={"image_id": "img_1", "file_hash": "abc"})

    def test_create_metadata_duplicate_raises_domain_error(self) -> None:
        def raise_duplicate(**_: Any) -> None:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "PutItem",
            )

        adapter = DummyAdapter()
        adapter.put_item = raise_duplicate
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(DuplicateImageError):
            repo.create_metadata(metadata={"image_id": "img_1", "file_hash": "abc"})

    def test_create_metadata_client_error_other_than_duplicate(self) -> None:
        def raise_client_error(**_: Any) -> None:
            raise ClientError(
                {"Error": {"Code": "ProvisionedThroughputExceededException"}},
                "PutItem",
            )

        adapter = DummyAdapter()
        adapter.put_item = raise_client_error
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.create_metadata(metadata={"image_id": "img_1"})

    def test_create_metadata_unexpected_exception(self) -> None:
        adapter = DummyAdapter()
        adapter.put_item = lambda **_: (_ for _ in ()).throw(Exception("boom"))
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.create_metadata(metadata={"image_id": "img_1"})

    def test_fetch_metadata_found(self) -> None:
        adapter = DummyAdapter()
        adapter.get_item = lambda **_: {"Item": {"image_id": "img_1", "user_id": "u1"}}
        repo = DynamoDBMetadata(adapter)

        result = repo.fetch_metadata(image_id="img_1")

        assert result is not None
        assert result["image_id"] == "img_1"

    def test_fetch_metadata_not_found(self) -> None:
        repo = DynamoDBMetadata(DummyAdapter())

        result = repo.fetch_metadata(image_id="missing")

        assert result is None

    def test_fetch_metadata_client_error(self) -> None:
        def raise_client_error(**_: Any) -> dict[str, Any]:
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "GetItem",
            )

        adapter = DummyAdapter()
        adapter.get_item = raise_client_error
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.fetch_metadata(image_id="img_1")

    def test_fetch_metadata_unexpected_exception(self) -> None:
        adapter = DummyAdapter()
        adapter.get_item = lambda **_: (_ for _ in ()).throw(Exception("boom"))
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.fetch_metadata(image_id="img_1")

    def test_remove_metadata_success(self) -> None:
        repo = DynamoDBMetadata(DummyAdapter())
        repo.remove_metadata(image_id="img_1")

    def test_remove_metadata_client_error(self) -> None:
        def raise_client_error(**_: Any) -> None:
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "DeleteItem",
            )

        adapter = DummyAdapter()
        adapter.delete_item = raise_client_error
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.remove_metadata(image_id="img_1")

    def test_remove_metadata_unexpected_exception(self) -> None:
        adapter = DummyAdapter()
        adapter.delete_item = lambda **_: (_ for _ in ()).throw(Exception("boom"))
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.remove_metadata(image_id="img_1")

    def test_list_user_images_invalid_limit(self) -> None:
        repo = DynamoDBMetadata(DummyAdapter())

        with pytest.raises(FilterError):
            repo.list_user_images(user_id="u1", limit=0)

    def test_list_user_images_invalid_date_range(self) -> None:
        repo = DynamoDBMetadata(DummyAdapter())

        with pytest.raises(FilterError):
            repo.list_user_images(
                user_id="u1",
                limit=10,
                start_date="2024-01-10",
                end_date="2024-01-01",
            )

    def test_list_user_images_success(self) -> None:
        adapter = DummyAdapter()
        adapter.query = lambda **_: {
            "Items": [
                {"image_id": "img_1", "user_id": "u1"},
                {"image_id": "img_2", "user_id": "u1"},
            ]
        }
        repo = DynamoDBMetadata(adapter)

        result = repo.list_user_images(user_id="u1", limit=10)
        assert len(result) == 2

    def test_list_user_images_client_error(self) -> None:
        def raise_client_error(**_: Any) -> dict[str, Any]:
            raise ClientError(
                {"Error": {"Code": "ValidationException"}},
                "Query",
            )

        adapter = DummyAdapter()
        adapter.query = raise_client_error
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.list_user_images(user_id="u1", limit=10)

    def test_list_user_images_unexpected_exception(self) -> None:
        adapter = DummyAdapter()
        adapter.query = lambda **_: (_ for _ in ()).throw(Exception("boom"))
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.list_user_images(user_id="u1", limit=10)

    def test_check_duplicate_image_true(self) -> None:
        adapter = DummyAdapter()
        adapter.query = lambda **_: {"Items": [{"image_id": "img_1"}]}
        repo = DynamoDBMetadata(adapter)

        assert repo.check_duplicate_image(user_id="u1", file_hash="abc") is True

    def test_check_duplicate_image_false(self) -> None:
        repo = DynamoDBMetadata(DummyAdapter())
        assert repo.check_duplicate_image(user_id="u1", file_hash="abc") is False

    def test_check_duplicate_image_client_error_returns_false(self) -> None:
        def raise_client_error(**_: Any) -> dict[str, Any]:
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "Query",
            )

        adapter = DummyAdapter()
        adapter.query = raise_client_error
        repo = DynamoDBMetadata(adapter)

        assert repo.check_duplicate_image(user_id="u1", file_hash="abc") is False

    def test_check_duplicate_image_unexpected_exception_raises(self) -> None:
        adapter = DummyAdapter()
        adapter.query = lambda **_: (_ for _ in ()).throw(Exception("boom"))
        repo = DynamoDBMetadata(adapter)

        with pytest.raises(MetadataOperationFailedError):
            repo.check_duplicate_image(user_id="u1", file_hash="abc")
