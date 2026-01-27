"""Thin DynamoDB adapter wrapping boto3 table operations."""

import os
from typing import Any, Protocol, cast

import boto3

from core.utils.constants import (
    ENV_AWS_ENDPOINT_URL,
    ENV_AWS_REGION,
    ENV_IMAGE_METADATA_TABLE_NAME,
)


class DynamoDBTable(Protocol):
    """Minimal DynamoDB Table protocol."""

    def put_item(self, *, Item: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...
    def get_item(self, *, Key: dict[str, Any]) -> dict[str, Any]: ...
    def delete_item(self, *, Key: dict[str, Any]) -> dict[str, Any]: ...
    def query(self, **kwargs: Any) -> dict[str, Any]: ...


class DynamoDBAdapter:
    """Low-level DynamoDB operations (mechanical, no error handling).

    This adapter:
    - Wraps boto3 DynamoDB resource
    - Does NOT handle errors (lets them bubble up)
    - Domain implementations catch and translate errors
    """

    def __init__(self) -> None:
        """Initialize DynamoDB table from environment."""
        table_name = os.getenv(ENV_IMAGE_METADATA_TABLE_NAME)
        if not table_name:
            raise RuntimeError(
                f"{ENV_IMAGE_METADATA_TABLE_NAME} environment variable is not set"
            )

        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=os.getenv(ENV_AWS_ENDPOINT_URL),
            region_name=os.getenv(ENV_AWS_REGION),
        )

        self.table: DynamoDBTable = cast(
            DynamoDBTable,
            dynamodb.Table(table_name),
        )

    def put_item(
        self,
        *,
        item: dict[str, Any],
        condition_expression: str | None = None,
    ) -> dict[str, Any]:
        """Insert item into DynamoDB.

        Raises boto3 exceptions - caught by domain implementation.
        """
        kwargs: dict[str, Any] = {"Item": item}

        if condition_expression:
            kwargs["ConditionExpression"] = condition_expression

        return self.table.put_item(**kwargs)

    def get_item(self, *, key: dict[str, Any]) -> dict[str, Any]:
        """Retrieve item by key.

        Raises boto3 exceptions - caught by domain implementation.
        """
        return self.table.get_item(Key=key)

    def delete_item(self, *, key: dict[str, Any]) -> dict[str, Any]:
        """Delete item by key.

        Raises boto3 exceptions - caught by domain implementation.
        """
        return self.table.delete_item(Key=key)

    def query(self, **kwargs: Any) -> dict[str, Any]:
        """Execute DynamoDB query.

        Raises boto3 exceptions - caught by domain implementation.
        """
        return self.table.query(**kwargs)
