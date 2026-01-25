"""
Business logic for image retrieval.

This module coordinates retrieval of image metadata and generation of
secure access URLs for image viewing and downloading.
"""

from typing import Any, Literal

from aws_lambda_powertools import Logger
from core.infrastructure.aws.dynamodb_metadata import DynamoDBMetadata
from core.infrastructure.aws.s3_image_storage import S3ImageStorage
from core.models.errors import (
    MetadataOperationFailedError,
    NotFoundError,
)

Metadata = dict[str, Any]

logger = Logger(UTC=True)


class GetService:
    """Application service responsible for retrieving images and metadata.

    This service orchestrates:
    - Fetching image metadata
    - Validating required metadata fields
    - Generating secure S3 pre-signed URLs
    """

    def __init__(self) -> None:
        self.storage = S3ImageStorage()
        self.metadata = DynamoDBMetadata()

    def generate_image_url(
        self,
        image_id: str,
        *,
        mode: Literal["view", "download"] = "view",
        expires_in: int = 300,
    ) -> tuple[str, Metadata]:
        """
        Generate a pre-signed S3 URL for viewing or downloading an image.

        Args:
            image_id: Unique image identifier
            mode: "view" (inline) or "download" (attachment)
            expires_in: URL expiration time in seconds

        Returns:
            Tuple of (pre_signed_url, image_metadata)

        Raises:
            NotFoundError: If metadata does not exist
            MetadataOperationFailedError: If metadata is invalid
        """
        logger.debug(
            "Generating image access URL",
            extra={"image_id": image_id, "mode": mode},
        )

        metadata = self._get_metadata_or_raise(image_id)

        s3_key = metadata.get("s3_key")
        if not isinstance(s3_key, str) or not s3_key:
            logger.error(
                "Metadata missing s3_key",
                extra={"image_id": image_id},
            )
            raise MetadataOperationFailedError(
                message="Image metadata is incomplete",
                error_code="METADATA_INVALID_STATE",
                details={"image_id": image_id},
            )

        disposition = "attachment" if mode == "download" else "inline"

        try:
            url = self.storage.generate_presigned_get_url(
                key=s3_key,
                expires_in=expires_in,
                content_disposition=(
                    f'{disposition}; filename="{metadata.get("image_name", "image")}"'
                ),
            )
        except Exception as exc:
            logger.exception(
                "Failed to generate pre-signed URL",
                extra={"image_id": image_id, "s3_key": s3_key},
            )
            raise MetadataOperationFailedError(
                message="Unable to generate image access URL",
                details={"image_id": image_id},
            ) from exc

        logger.info(
            "Pre-signed URL generated successfully",
            extra={"image_id": image_id, "mode": mode},
        )

        return url, metadata

    def get_metadata(self, image_id: str) -> Metadata | None:
        """Retrieve image metadata only."""
        metadata = self.metadata.fetch_metadata(image_id=image_id)

        if metadata is None:
            return None

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

        return metadata

    def _get_metadata_or_raise(self, image_id: str) -> Metadata:
        metadata = self.get_metadata(image_id)

        if metadata is None:
            logger.warning(
                "Image metadata not found",
                extra={"image_id": image_id},
            )
            raise NotFoundError(
                message="Image not found",
                details={"image_id": image_id},
            )

        return metadata
