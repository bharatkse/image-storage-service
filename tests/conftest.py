"""
Pytest configuration and fixtures for image-stream tests.
Provides AWS mocking, DynamoDB and S3 fixtures with proper cleanup.
"""

import os
from collections.abc import Callable
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws


@pytest.fixture(scope="function")
def aws_mock():
    with mock_aws():
        yield


@pytest.fixture(scope="function")
def dynamodb_client(aws_mock):
    return boto3.client("dynamodb", region_name=os.getenv("AWS_REGION"))


@pytest.fixture(scope="function")
def dynamodb_resource(aws_mock):
    return boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION"))


def _create_dynamodb_table(dynamodb_resource):
    """Helper to create DynamoDB table with GSIs."""
    table_name = os.getenv("IMAGE_METADATA_TABLE_NAME")

    return dynamodb_resource.create_table(
        TableName=table_name,
        BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": "image_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "image_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
            {"AttributeName": "image_name", "AttributeType": "S"},
            {"AttributeName": "file_hash", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user-created-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "user-name-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "image_name", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "user-filehash-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "file_hash", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "KEYS_ONLY"},
            },
        ],
    )


def _cleanup_dynamodb_items(table):
    """Helper to delete all items from DynamoDB table efficiently."""
    try:
        response = table.scan(ProjectionExpression="image_id")
        items = response.get("Items", [])

        if items:
            with table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={"image_id": item["image_id"]})

        while "LastEvaluatedKey" in response:
            response = table.scan(
                ProjectionExpression="image_id",
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items = response.get("Items", [])
            if items:
                with table.batch_writer() as batch:
                    for item in items:
                        batch.delete_item(Key={"image_id": item["image_id"]})
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise


@pytest.fixture(scope="function")
def dynamodb_table(dynamodb_resource):
    """
    Create and manage DynamoDB table for testing.

    Cleanup Strategy:
    - Items are deleted after each test (teardown)
    - Table is NOT deleted (reused, moto cleans up on context exit)
    """
    table_name = os.getenv("IMAGE_METADATA_TABLE_NAME")

    try:
        table = dynamodb_resource.Table(table_name)
        table.load()
    except ClientError:
        table = _create_dynamodb_table(dynamodb_resource)
        table.wait_until_exists()

    yield table

    _cleanup_dynamodb_items(table)


@pytest.fixture
def dynamodb_put_item(dynamodb_table) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """
    Helper to insert a single item into DynamoDB.

    Usage:
        item = dynamodb_put_item({"image_id": "img_1", "user_id": "john"})
    """

    def _put(item: dict[str, Any]) -> dict[str, Any]:
        dynamodb_table.put_item(Item=item)
        return item

    return _put


@pytest.fixture
def dynamodb_put_multiple_items(
    dynamodb_table,
) -> Callable[[list[dict[str, Any]]], list[dict[str, Any]]]:
    """
    Helper to insert multiple items into DynamoDB efficiently.

    Usage:
        items = dynamodb_put_multiple_items([item1, item2, item3])
    """

    def _put(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with dynamodb_table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
        return items

    return _put


@pytest.fixture
def dynamodb_get_item(dynamodb_table) -> Callable[[str], dict[str, Any] | None]:
    """
    Helper to get a single item from DynamoDB.

    Usage:
        item = dynamodb_get_item("img_123")
    """

    def _get(image_id: str) -> dict[str, Any] | None:
        response: dict[str, Any] = dynamodb_table.get_item(Key={"image_id": image_id})
        item: dict[str, Any] | None = response.get("Item")
        return item

    return _get


@pytest.fixture
def dynamodb_delete_item(dynamodb_table) -> Callable[[str], None]:
    """
    Helper to delete a single item from DynamoDB.

    Usage:
        dynamodb_delete_item("img_123")
    """

    def _delete(image_id: str) -> None:
        dynamodb_table.delete_item(Key={"image_id": image_id})

    return _delete


@pytest.fixture(scope="function")
def s3_client(aws_mock):
    """S3 client for bucket operations."""
    return boto3.client("s3", region_name=os.getenv("AWS_REGION"))


def _cleanup_s3_objects(s3_client, bucket_name):
    """Helper to delete all objects from S3 bucket efficiently."""
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            objects = page.get("Contents", [])
            if objects:
                delete_keys = [{"Key": obj["Key"]} for obj in objects]
                s3_client.delete_objects(
                    Bucket=bucket_name, Delete={"Objects": delete_keys}
                )
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchBucket":
            raise


@pytest.fixture(scope="function")
def s3_bucket(s3_client):
    """
    Create and manage S3 bucket for testing.

    Cleanup Strategy:
    - Objects are deleted after each test (teardown)
    - Bucket is NOT deleted (reused, moto cleans up on context exit)
    """
    bucket_name = os.getenv("IMAGE_S3_BUCKET_NAME")

    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise

    yield s3_client

    _cleanup_s3_objects(s3_client, bucket_name)


@pytest.fixture
def s3_put_object(s3_client) -> Callable[[str, bytes, str], dict[str, Any]]:
    """
    Helper to upload an object to S3.

    Usage:
        response = s3_put_object("images/user/img.jpg", image_bytes, "image/jpeg")
    """

    def _put(key: str, body: bytes, content_type: str = "application/octet-stream"):
        bucket_name = os.getenv("IMAGE_S3_BUCKET_NAME")
        return s3_client.put_object(
            Bucket=bucket_name, Key=key, Body=body, ContentType=content_type
        )

    return _put


@pytest.fixture
def s3_get_object(s3_client) -> Callable[[str], bytes]:
    """
    Helper to get an object from S3.

    Usage:
        content = s3_get_object("images/user/img.jpg")
    """

    def _get(key: str) -> bytes:
        bucket_name = os.getenv("IMAGE_S3_BUCKET_NAME")
        response: dict[str, Any] = s3_client.get_object(
            Bucket=bucket_name,
            Key=key,
        )
        body = response["Body"]
        data: bytes = body.read()
        return data

    return _get


@pytest.fixture
def s3_delete_object(s3_client) -> Callable[[str], None]:
    """
    Helper to delete an object from S3.

    Usage:
        s3_delete_object("images/user/img.jpg")
    """

    def _delete(key: str) -> None:
        bucket_name = os.getenv("IMAGE_S3_BUCKET_NAME")
        s3_client.delete_object(Bucket=bucket_name, Key=key)

    return _delete


@pytest.fixture
def sample_image_metadata() -> dict[str, Any]:
    """Single image metadata for testing."""
    return {
        "image_id": "img_1",
        "user_id": "john",
        "image_name": "a.jpg",
        "description": "First image",
        "tags": ["alpha", "test"],
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": None,
        "s3_key": "images/john/img_1.jpg",
        "file_size": 100,
        "mime_type": "image/jpeg",
    }


@pytest.fixture
def multiple_image_metadata_items() -> list[dict[str, Any]]:
    """Multiple image metadata items for testing list/filter operations."""
    return [
        {
            "image_id": "img_2",
            "user_id": "john",
            "image_name": "b.png",
            "description": "Second image",
            "tags": ["beta"],
            "created_at": "2024-01-02T10:00:00Z",
            "updated_at": None,
            "s3_key": "images/john/img_2.png",
            "file_size": 200,
            "mime_type": "image/png",
        },
        {
            "image_id": "img_3",
            "user_id": "alice",
            "image_name": "cat.png",
            "description": "Cat photo",
            "tags": ["cat", "animal"],
            "created_at": "2024-01-03T10:00:00Z",
            "updated_at": None,
            "s3_key": "images/alice/img_3.png",
            "file_size": 300,
            "mime_type": "image/png",
        },
        {
            "image_id": "img_4",
            "user_id": "john",
            "image_name": "sunset.jpg",
            "description": "Sunset photo",
            "tags": ["sunset", "nature"],
            "created_at": "2024-01-04T10:00:00Z",
            "updated_at": None,
            "s3_key": "images/john/img_4.jpg",
            "file_size": 400,
            "mime_type": "image/jpeg",
        },
    ]


@pytest.fixture
def dynamodb_with_multiple_items(
    dynamodb_put_multiple_items,
    multiple_image_metadata_items,
) -> list[dict[str, Any]]:
    """DynamoDB table pre-populated with multiple items."""
    items: list[dict[str, Any]] = dynamodb_put_multiple_items(
        multiple_image_metadata_items
    )
    return items


@pytest.fixture
def sample_image_binary() -> bytes:
    """Sample binary image data (1x1 PNG)."""
    import base64

    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    return base64.b64decode(png_base64)


@pytest.fixture
def sample_jpeg_binary() -> bytes:
    """Sample binary JPEG data (minimal valid JPEG)."""
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
        b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
        b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08"
        b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\xff\xc4\x00\x14\x10"
        b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\x00\xff\xd9"
    )
