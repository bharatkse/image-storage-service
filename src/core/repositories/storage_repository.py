"""Abstract contract for image file storage."""

from abc import ABC, abstractmethod


class ImageStorageRepository(ABC):
    """Contract for storing and retrieving image files.

    Implementations could be S3, GCS, local disk, etc.
    Handlers depend on this interface, not the implementation.
    """

    @abstractmethod
    def upload_image(
        self,
        *,
        image_id: str,
        user_id: str,
        file_data: bytes,
        mime_type: str,
    ) -> str:
        """Upload image and return storage key.

        Args:
            image_id: Unique image identifier
            user_id: Owner of the image
            file_data: Binary image content
            mime_type: MIME type (e.g., 'image/jpeg')

        Returns:
            Storage key for later retrieval

        Raises:
            S3Error: If upload fails
        """

    @abstractmethod
    def download_image(self, *, key: str) -> tuple[bytes, str, int]:
        """Download image by key.

        Args:
            key: Storage key from upload

        Returns:
            Tuple of (content_bytes, content_type, content_length)

        Raises:
            FileNotFoundError: If image doesn't exist
            S3Error: If download fails
        """

    @abstractmethod
    def remove_image(self, *, key: str) -> None:
        """Delete image by key.

        Args:
            key: Storage key from upload

        Raises:
            S3Error: If deletion fails
        """
