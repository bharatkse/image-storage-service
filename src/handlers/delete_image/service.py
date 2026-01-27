"""Business logic for image deletion.

This module coordinates deletion of an image and its associated metadata.
It ensures the image is removed from storage first, followed by metadata
cleanup, while translating failures into domain-specific errors.
"""

from typing import Any

from aws_lambda_powertools import Logger

from core.infrastructure.aws.dynamodb_metadata import DynamoDBMetadata
from core.infrastructure.aws.s3_image_storage import S3ImageStorage
from core.models.errors import (
    MetadataOperationFailedError,
    NotFoundError,
    S3Error,
)
from core.utils.time import utc_now_iso

logger = Logger(UTC=True)


class DeleteService:
    """Application service responsible for deleting images.

    This service orchestrates:
    - Validation that the image exists
    - Deletion of the image object from storage
    - Removal of metadata from the database

    It does not perform low-level infrastructure operations directly.
    """

    def __init__(self) -> None:
        """Initialize the delete service with required infrastructure dependencies."""
        self.storage = S3ImageStorage()
        self.metadata = DynamoDBMetadata()

    def delete_image(self, image_id: str) -> dict[str, Any]:
        """Delete an image and its metadata.

        The deletion flow is:
        1. Fetch metadata to confirm the image exists and obtain the storage key
        2. Delete the image from object storage
        3. Delete the associated metadata record

        Args:
            image_id: Unique identifier of the image to delete

        Returns:
            A dictionary containing deletion confirmation details

        Raises:
            NotFoundError: If the image metadata does not exist
            S3Error: If storage deletion fails
            MetadataOperationFailedError: If metadata deletion fails
        """
        logger.debug("Starting image deletion", extra={"image_id": image_id})

        # Step 1: Fetch metadata to validate existence and locate the storage object
        metadata = self.metadata.fetch_metadata(image_id=image_id)

        if metadata is None or not metadata:
            logger.warning(
                "Image metadata not found",
                extra={"image_id": image_id},
            )
            raise NotFoundError(
                message="Image not found",
                details={"image_id": image_id},
            )

        if not isinstance(metadata, dict):
            logger.error(
                "Invalid metadata format",
                extra={"image_id": image_id},
            )
            raise MetadataOperationFailedError(
                message="Invalid image metadata format",
                error_code="METADATA_INVALID_FORMAT",
                details={"image_id": image_id},
            )

        s3_key = metadata.get("s3_key")
        if not isinstance(s3_key, str) or not s3_key:
            logger.error(
                "Image metadata missing storage key",
                extra={"image_id": image_id},
            )
            raise MetadataOperationFailedError(
                message="Image metadata is incomplete",
                error_code="METADATA_INVALID_STATE",
                details={"image_id": image_id},
            )

        # Step 2: Delete the image from object storage
        # Storage deletion is performed first to avoid orphaned objects
        try:
            self.storage.remove_image(key=s3_key)
        except Exception as exc:
            logger.exception(
                "Failed to delete image from storage",
                extra={"image_id": image_id, "s3_key": s3_key},
            )
            raise S3Error(
                message="Unable to delete image from storage",
                details={"image_id": image_id},
            ) from exc

        # Step 3: Delete metadata from the database
        try:
            self.metadata.remove_metadata(image_id=image_id)
        except Exception as exc:
            logger.exception(
                "Failed to delete image metadata",
                extra={"image_id": image_id},
            )
            raise MetadataOperationFailedError(
                message="Unable to delete image metadata",
                error_code="METADATA_DELETE_FAILED",
                details={"image_id": image_id},
            ) from exc

        # Successful deletion response
        logger.info("Image deleted successfully", extra={"image_id": image_id})

        return {
            "image_id": image_id,
            "s3_key": s3_key,
            "deleted_at": utc_now_iso(),
        }
