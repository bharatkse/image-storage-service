"""DynamoDB-backed implementation of ImageMetadataRepository."""

from typing import Any

from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from core.infrastructure.adapters.dynamodb_adapter import DynamoDBAdapter
from core.models.errors import (
    DuplicateImageError,
    FilterError,
    MetadataOperationFailedError,
)
from core.repositories.metadata_repository import ImageMetadataRepository
from core.utils.constants import (
    ERROR_CODE_METADATA_CREATE_FAILED,
    ERROR_CODE_METADATA_DELETE_FAILED,
    ERROR_CODE_METADATA_DUPLICATE_CHECK_FAILED,
    ERROR_CODE_METADATA_FETCH_FAILED,
    ERROR_CODE_METADATA_LIST_FAILED,
    MAX_LIMIT,
)

Metadata = dict[str, Any]

logger = Logger(UTC=True)


class DynamoDBMetadata(ImageMetadataRepository):
    """DynamoDB-backed metadata storage with error handling.

    All boto3 errors are caught and translated into
    domain-specific errors with stable semantics.
    """

    def __init__(self, adapter: DynamoDBAdapter | None = None) -> None:
        """Initialize with DynamoDB adapter."""
        self._db = adapter or DynamoDBAdapter()

    def create_metadata(self, *, metadata: Metadata) -> None:
        """Create metadata for an image.

        Raises:
            DuplicateImageError: If file hash already exists
            MetadataOperationFailedError: If creation fails
        """
        image_id = metadata.get("image_id")
        logger.debug("Creating metadata", extra={"image_id": image_id})

        try:
            self._db.put_item(
                item=metadata,
                condition_expression="attribute_not_exists(file_hash)",
            )
            logger.info("Metadata created", extra={"image_id": image_id})

        except ClientError as exc:
            logger.error("DynamoDB put_item failed", extra={"image_id": image_id})

            if (
                exc.response.get("Error", {}).get("Code")
                == "ConditionalCheckFailedException"
            ):
                raise DuplicateImageError(
                    message="This image already exists",
                    details={"image_id": image_id},
                ) from exc

            raise MetadataOperationFailedError(
                message="Unable to save image metadata at this time",
                error_code=ERROR_CODE_METADATA_CREATE_FAILED,
                details={"image_id": image_id},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error creating metadata")
            raise MetadataOperationFailedError(
                message="Unable to save image metadata at this time",
                error_code=ERROR_CODE_METADATA_CREATE_FAILED,
                details={"image_id": image_id},
            ) from exc

    def fetch_metadata(self, *, image_id: str) -> Metadata | None:
        """Fetch metadata for a single image.

        Raises:
            MetadataOperationFailedError: If fetch fails
        """
        logger.debug("Fetching metadata", extra={"image_id": image_id})

        try:
            response = self._db.get_item(key={"image_id": image_id})
            item = response.get("Item")

            if item is None:
                return None

            if not isinstance(item, dict):
                raise MetadataOperationFailedError(
                    message="Invalid image metadata format",
                    error_code=ERROR_CODE_METADATA_FETCH_FAILED,
                    details={"image_id": image_id},
                )

            return item

        except ClientError as exc:
            logger.error("DynamoDB get_item failed", extra={"image_id": image_id})
            raise MetadataOperationFailedError(
                message="Unable to retrieve image metadata",
                error_code=ERROR_CODE_METADATA_FETCH_FAILED,
                details={"image_id": image_id},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error fetching metadata")
            raise MetadataOperationFailedError(
                message="Unable to retrieve image metadata",
                error_code=ERROR_CODE_METADATA_FETCH_FAILED,
                details={"image_id": image_id},
            ) from exc

    def remove_metadata(self, *, image_id: str) -> None:
        """Remove metadata for an image.

        Raises:
            MetadataOperationFailedError: If deletion fails
        """
        logger.debug("Removing metadata", extra={"image_id": image_id})

        try:
            self._db.delete_item(key={"image_id": image_id})
            logger.info("Metadata removed", extra={"image_id": image_id})

        except ClientError as exc:
            logger.error("DynamoDB delete_item failed", extra={"image_id": image_id})
            raise MetadataOperationFailedError(
                message="Unable to delete image metadata",
                error_code=ERROR_CODE_METADATA_DELETE_FAILED,
                details={"image_id": image_id},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error removing metadata")
            raise MetadataOperationFailedError(
                message="Unable to delete image metadata",
                error_code=ERROR_CODE_METADATA_DELETE_FAILED,
                details={"image_id": image_id},
            ) from exc

    def list_user_images(
        self,
        *,
        user_id: str,
        limit: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Metadata]:
        """List images for a user with optional date filtering.

        NOTE:
        - Date filtering is performed at the DynamoDB level.
        - created_at must be stored in ISO-8601 UTC format.
        """

        logger.debug(
            "Listing user images",
            extra={
                "user_id": user_id,
                "limit": limit,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        if limit < 1 or limit > MAX_LIMIT:
            raise FilterError(
                message="Limit must be between 1 and 100",
                details={"limit": limit},
            )

        if start_date and end_date and start_date > end_date:
            raise FilterError(
                message="Start date must be before end date",
                details={"start_date": start_date, "end_date": end_date},
            )

        key_condition = Key("user_id").eq(user_id)

        if start_date and end_date:
            key_condition &= Key("created_at").between(start_date, end_date)
        elif start_date:
            key_condition &= Key("created_at").gte(start_date)
        elif end_date:
            key_condition &= Key("created_at").lte(end_date)

        query_kwargs: dict[str, Any] = {
            "IndexName": "user-created-index",
            "KeyConditionExpression": key_condition,
            "ScanIndexForward": False,
        }

        items: list[Metadata] = []
        last_evaluated_key: dict[str, Any] | None = None

        try:
            while True:
                if last_evaluated_key:
                    query_kwargs["ExclusiveStartKey"] = last_evaluated_key

                response = self._db.query(**query_kwargs)
                page_items = response.get("Items", [])

                if not isinstance(page_items, list):
                    raise MetadataOperationFailedError(
                        message="Invalid query response from DynamoDB",
                        error_code=ERROR_CODE_METADATA_LIST_FAILED,
                        details={"user_id": user_id},
                    )

                items.extend(page_items)
                last_evaluated_key = response.get("LastEvaluatedKey")

                if not last_evaluated_key:
                    break

            logger.info(
                "User images listed",
                extra={
                    "user_id": user_id,
                    "count": len(items),
                },
            )

            return items

        except ClientError as exc:
            logger.error("DynamoDB query failed", extra={"user_id": user_id})

            raise MetadataOperationFailedError(
                message="Unable to list images for this user",
                error_code=ERROR_CODE_METADATA_LIST_FAILED,
                details={"user_id": user_id},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error listing images")
            raise MetadataOperationFailedError(
                message="Unable to list images for this user",
                error_code=ERROR_CODE_METADATA_LIST_FAILED,
                details={"user_id": user_id},
            ) from exc

    def check_duplicate_image(
        self,
        *,
        user_id: str,
        file_hash: str,
    ) -> bool:
        """Check whether an image already exists for a user.

        Raises:
            MetadataOperationFailedError: If check fails
        """
        logger.debug("Checking for duplicate", extra={"user_id": user_id})

        try:
            response = self._db.query(
                IndexName="user-filehash-index",
                KeyConditionExpression=(
                    Key("user_id").eq(user_id) & Key("file_hash").eq(file_hash)
                ),
                Limit=1,
            )

            items = response.get("Items", [])
            return isinstance(items, list) and bool(items)

        except ClientError:
            logger.warning("Duplicate check unavailable, skipping")
            return False

        except Exception as exc:
            logger.exception("Unexpected error checking duplicate")
            raise MetadataOperationFailedError(
                message="Unable to verify duplicate image",
                error_code=ERROR_CODE_METADATA_DUPLICATE_CHECK_FAILED,
                details={"user_id": user_id},
            ) from exc
