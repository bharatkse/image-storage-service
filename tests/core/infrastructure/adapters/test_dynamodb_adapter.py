import pytest
from botocore.exceptions import ClientError
from core.infrastructure.adapters.dynamodb_adapter import DynamoDBAdapter
from core.utils.constants import ENV_IMAGE_METADATA_TABLE_NAME


class TestDynamoDBAdapter:
    def test_init_missing_table_env(self, monkeypatch):
        monkeypatch.delenv(ENV_IMAGE_METADATA_TABLE_NAME, raising=False)

        with pytest.raises(RuntimeError):
            DynamoDBAdapter()

    def test_put_and_get_item_success(self, dynamodb_table):
        adapter = DynamoDBAdapter()

        item = {
            "image_id": "img_1",
            "user_id": "john",
        }

        adapter.put_item(item=item)

        response = adapter.get_item(key={"image_id": "img_1"})

        assert response["Item"]["image_id"] == "img_1"
        assert response["Item"]["user_id"] == "john"

    def test_put_item_with_condition_expression(self, dynamodb_table):
        adapter = DynamoDBAdapter()

        item = {
            "image_id": "img_cond",
            "user_id": "john",
        }

        adapter.put_item(
            item=item,
            condition_expression="attribute_not_exists(image_id)",
        )

        with pytest.raises(ClientError):
            adapter.put_item(
                item=item,
                condition_expression="attribute_not_exists(image_id)",
            )

    def test_delete_item_success(self, dynamodb_table):
        adapter = DynamoDBAdapter()

        adapter.put_item(item={"image_id": "img_del"})
        adapter.delete_item(key={"image_id": "img_del"})

        response = adapter.get_item(key={"image_id": "img_del"})
        assert "Item" not in response

    def test_query_returns_items(self, dynamodb_table):
        adapter = DynamoDBAdapter()

        adapter.put_item(
            item={
                "image_id": "img_1",
                "user_id": "john",
                "created_at": "2024-01-01T10:00:00Z",
            }
        )
        adapter.put_item(
            item={
                "image_id": "img_2",
                "user_id": "john",
                "created_at": "2024-01-02T10:00:00Z",
            }
        )

        response = adapter.query(
            IndexName="user-created-index",
            KeyConditionExpression="user_id = :u",
            ExpressionAttributeValues={":u": "john"},
        )

        assert len(response["Items"]) == 2

    def test_get_item_bubbles_client_error(self, monkeypatch, dynamodb_table):
        adapter = DynamoDBAdapter()

        def raise_error(**_):
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "GetItem",
            )

        monkeypatch.setattr(adapter.table, "get_item", raise_error)

        with pytest.raises(ClientError):
            adapter.get_item(key={"image_id": "img_x"})

    def test_delete_item_bubbles_client_error(self, monkeypatch, dynamodb_table):
        adapter = DynamoDBAdapter()

        def raise_error(**_):
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "DeleteItem",
            )

        monkeypatch.setattr(adapter.table, "delete_item", raise_error)

        with pytest.raises(ClientError):
            adapter.delete_item(key={"image_id": "img_x"})

    def test_query_bubbles_client_error(self, monkeypatch, dynamodb_table):
        adapter = DynamoDBAdapter()

        def raise_error(**_):
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "Query",
            )

        monkeypatch.setattr(adapter.table, "query", raise_error)

        with pytest.raises(ClientError):
            adapter.query(IndexName="idx")
