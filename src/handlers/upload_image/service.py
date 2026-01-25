"""Business logic for image upload operations.

This module coordinates validation, storage, and metadata persistence
for image uploads while translating failures into domain-specific errors.
"""

import base64
import hashlib
import uuid
from typing import Any

from aws_lambda_powertools import Logger
from core.infrastructure.aws.dynamodb_metadata import DynamoDBMetadata
from core.infrastructure.aws.s3_image_storage import S3ImageStorage
from core.models.errors import (
    DuplicateImageError,
    ImageUploadFailedError,
    MetadataOperationFailedError,
    ValidationError,
)
from core.models.image import ImageMetadata
from core.utils.constants import ALLOWED_MIME_TYPES
from core.utils.mime import detect_mime_type
from core.utils.time import utc_now_iso

Metadata = dict[str, Any]

logger = Logger(UTC=True)


class UploadService:
    """Application service responsible for image uploads.

    This service orchestrates:
    - File decoding and validation
    - Duplicate detection
    - Uploading image content to storage
    - Persisting image metadata
    """

    def __init__(self) -> None:
        """Initialize the upload service with required infrastructure dependencies."""
        self.storage = S3ImageStorage()
        self.metadata = DynamoDBMetadata()

    @staticmethod
    def decode_file(encoded: str) -> bytes:
        """Decode base64-encoded image data.

        Args:
            encoded: Base64-encoded image content

        Returns:
            Decoded image bytes

        Raises:
            ValidationError: If decoding fails
        """
        try:
            return base64.b64decode(encoded)
        except Exception as exc:
            logger.exception("Failed to decode base64 image data")
            raise ValidationError(
                message="Invalid image data",
                details={"encoding": "base64"},
            ) from exc

    @staticmethod
    def generate_image_id() -> str:
        """Generate a unique image identifier."""
        return f"img_{uuid.uuid4().hex}"

    def upload_image(
        self,
        *,
        user_id: str,
        image_name: str,
        file_data: bytes,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Metadata:
        """Upload an image and persist its metadata.

        The upload flow is:
        1. Detect and validate MIME type
        2. Check for duplicate image content
        3. Upload image to object storage
        4. Persist image metadata
        5. Roll back storage if metadata persistence fails

        Args:
            user_id: Owner of the image
            image_name: Human-readable image name
            file_data: Raw image bytes
            description: Optional image description
            tags: Optional list of tags

        Returns:
            Persisted image metadata

        Raises:
            ValidationError: If the file type is not supported
            DuplicateImageError: If the image already exists
            ImageUploadFailedError: If storage upload fails
            MetadataOperationFailedError: If metadata persistence fails
        """
        logger.debug("Starting image upload", extra={"user_id": user_id})

        # Step 1: Detect and validate MIME type
        mime_type = detect_mime_type(file_data)
        if mime_type not in ALLOWED_MIME_TYPES:
            logger.warning(
                "Unsupported MIME type",
                extra={"mime_type": mime_type},
            )
            raise ValidationError(
                message="Unsupported image type",
                details={"mime_type": mime_type},
            )

        # Step 2: Detect duplicate image by content hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        if self.metadata.check_duplicate_image(
            user_id=user_id,
            file_hash=file_hash,
        ):
            logger.info(
                "Duplicate image detected",
                extra={"user_id": user_id},
            )
            raise DuplicateImageError(
                message="This image already exists",
                details={"user_id": user_id},
            )

        # Step 3: Upload image to storage
        image_id = self.generate_image_id()
        timestamp = utc_now_iso()

        try:
            s3_key = self.storage.upload_image(
                image_id=image_id,
                user_id=user_id,
                file_data=file_data,
                mime_type=mime_type,
            )
        except Exception as exc:
            logger.exception("Image upload to storage failed")
            raise ImageUploadFailedError(
                message="Unable to upload image",
                details={"image_id": image_id},
            ) from exc

        # Step 4: Build metadata object
        metadata: dict[str, Any] = ImageMetadata(
            image_id=image_id,
            user_id=user_id,
            image_name=image_name,
            description=description,
            tags=tags,
            created_at=timestamp,
            updated_at=None,
            s3_key=s3_key,
            file_size=len(file_data),
            mime_type=mime_type,
            file_hash=file_hash,
        ).model_dump()

        # Step 5: Persist metadata (rollback storage on failure)
        try:
            self.metadata.create_metadata(metadata=metadata)
        except Exception as exc:
            logger.exception("Failed to persist image metadata")

            # Best-effort cleanup to avoid orphaned storage objects
            try:
                self.storage.remove_image(key=s3_key)
            except Exception:
                logger.warning(
                    "Failed to clean up uploaded image after metadata failure",
                    extra={"s3_key": s3_key},
                )

            raise MetadataOperationFailedError(
                message="Unable to save image metadata",
                error_code="METADATA_CREATE_FAILED",
                details={"image_id": image_id},
            ) from exc

        logger.info(
            "Image uploaded successfully",
            extra={"image_id": image_id, "user_id": user_id},
        )
        return metadata
