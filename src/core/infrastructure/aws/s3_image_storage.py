"""S3-backed implementation of ImageStorageRepository."""

from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from core.infrastructure.adapters.s3_adapter import S3Adapter, S3AdapterProtocol
from core.models.errors import (
    NotFoundError,
    S3Error,
)
from core.repositories.storage_repository import ImageStorageRepository
from core.utils.constants import (
    ERROR_CODE_IMAGE_DELETE_FAILED,
    ERROR_CODE_IMAGE_DOWNLOAD_FAILED,
    ERROR_CODE_IMAGE_PRESIGNED_URL_FAILED,
    ERROR_CODE_IMAGE_UPLOAD_FAILED,
    MIME_TYPE_EXTENSION_MAP,
)

logger = Logger(UTC=True)


class S3ImageStorage(ImageStorageRepository):
    """Image storage implementation backed by Amazon S3."""

    def __init__(self, adapter: S3AdapterProtocol | None = None) -> None:
        """Create storage using the provided S3 adapter."""
        self._s3: S3AdapterProtocol = adapter or S3Adapter()

    def upload_image(
        self,
        *,
        image_id: str,
        user_id: str,
        file_data: bytes,
        mime_type: str,
    ) -> str:
        """Upload image bytes to S3 and return the object key."""
        extension = self._get_extension(mime_type)
        key = f"images/{user_id}/{image_id}.{extension}"

        logger.debug(
            "Uploading image",
            extra={
                "image_id": image_id,
                "user_id": user_id,
                "key": key,
                "size": len(file_data),
            },
        )

        try:
            self._s3.put_object(
                key=key,
                body=file_data,
                content_type=mime_type,
                metadata={
                    "image_id": image_id,
                    "user_id": user_id,
                },
            )
            logger.info("Image uploaded successfully", extra={"key": key})
            return key

        except ClientError as exc:
            logger.error("S3 upload failed", extra={"key": key})
            raise S3Error(
                message="Unable to upload image at this time",
                error_code=ERROR_CODE_IMAGE_UPLOAD_FAILED,
                details={"image_id": image_id},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error uploading image")
            raise S3Error(
                message="Unable to upload image at this time",
                error_code=ERROR_CODE_IMAGE_UPLOAD_FAILED,
                details={"image_id": image_id},
            ) from exc

    def generate_presigned_get_url(
        self,
        *,
        key: str,
        expires_in: int = 300,
        content_disposition: str | None = None,
    ) -> str:
        """Generate a pre-signed S3 URL for reading an image object."""
        logger.debug(
            "Generating pre-signed S3 URL",
            extra={"key": key, "expires_in": expires_in},
        )

        try:
            params: dict[str, Any] = {"Key": key}

            if content_disposition:
                params["ResponseContentDisposition"] = content_disposition

            url: str = self._s3.generate_presigned_url(
                method="get_object",
                params=params,
                expires_in=expires_in,
            )

            return url
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise NotFoundError(
                    message="Image not found",
                    details={"key": key},
                ) from exc

            logger.error("Failed to generate pre-signed URL", extra={"key": key})
            raise S3Error(
                message="Unable to generate image access URL",
                error_code=ERROR_CODE_IMAGE_PRESIGNED_URL_FAILED,
                details={"key": key},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error generating pre-signed URL")
            raise S3Error(
                message="Unable to generate image access URL",
                error_code=ERROR_CODE_IMAGE_PRESIGNED_URL_FAILED,
                details={"key": key},
            ) from exc

    def download_image(self, *, key: str) -> tuple[bytes, str, int]:
        """Download image bytes directly from S3 (legacy path)."""
        logger.debug("Downloading image (legacy)", extra={"key": key})

        try:
            response = self._s3.get_object(key=key)
            body = response["Body"].read()
            content_type = response.get("ContentType", "application/octet-stream")
            content_length = response.get("ContentLength", len(body))

            logger.info(
                "Image downloaded successfully",
                extra={"key": key, "size": content_length},
            )

            return body, content_type, content_length

        except ClientError as exc:
            logger.error("S3 download failed", extra={"key": key})

            if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise NotFoundError(
                    message="Image not found",
                    details={"key": key},
                ) from exc

            raise S3Error(
                message="Unable to download image at this time",
                error_code=ERROR_CODE_IMAGE_DOWNLOAD_FAILED,
                details={"key": key},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error downloading image")
            raise S3Error(
                message="Unable to download image at this time",
                error_code=ERROR_CODE_IMAGE_DOWNLOAD_FAILED,
                details={"key": key},
            ) from exc

    def remove_image(self, *, key: str) -> None:
        """Delete an image object from S3."""
        logger.debug("Deleting image", extra={"key": key})

        try:
            self._s3.delete_object(key=key)
            logger.info("Image deleted successfully", extra={"key": key})

        except ClientError as exc:
            logger.error("S3 deletion failed", extra={"key": key})
            raise S3Error(
                message="Unable to delete image at this time",
                error_code=ERROR_CODE_IMAGE_DELETE_FAILED,
                details={"key": key},
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error deleting image")
            raise S3Error(
                message="Unable to delete image at this time",
                error_code=ERROR_CODE_IMAGE_DELETE_FAILED,
                details={"key": key},
            ) from exc

    @staticmethod
    def _get_extension(mime_type: str) -> str:
        """Return file extension for a given MIME type."""
        ext = MIME_TYPE_EXTENSION_MAP.get(mime_type)
        if not ext:
            return "bin"

        # MIME_TYPE_EXTENSION_MAP values are tuple[str, ...]
        return ext[0]
