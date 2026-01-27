"""Abstract contract for image metadata persistence."""

from abc import ABC, abstractmethod
from typing import Any

Metadata = dict[str, Any]


class ImageMetadataRepository(ABC):
    """Contract for storing and retrieving image metadata.

    Implementations could be DynamoDB, PostgreSQL, MongoDB, etc.
    Handlers depend on this interface, not the implementation.
    """

    @abstractmethod
    def create_metadata(self, *, metadata: Metadata) -> None:
        """Create metadata for an image.

        Args:
            metadata: Image metadata dict with required keys:
                     - image_id: str
                     - user_id: str
                     - file_hash: str
                     - created_at: str (ISO-8601 UTC format)

        Raises:
            DuplicateImageError: If image already exists for this user
            DynamoDBError: If creation fails for other reasons
        """

    @abstractmethod
    def fetch_metadata(self, *, image_id: str) -> Metadata | None:
        """Fetch metadata for a single image.

        Args:
            image_id: Unique image identifier

        Returns:
            Metadata dict or None if not found

        Raises:
            DynamoDBError: If fetch fails
        """

    @abstractmethod
    def remove_metadata(self, *, image_id: str) -> None:
        """Remove metadata for an image.

        Args:
            image_id: Unique image identifier

        Raises:
            DynamoDBError: If deletion fails
        """

    @abstractmethod
    def list_user_images(
        self,
        *,
        user_id: str,
        limit: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Metadata]:
        """List images for a user with optional date filtering.

        Args:
            user_id: Image owner
            limit: Maximum results (1-100)
            start_date: Optional filter start date (ISO-8601 format)
            end_date: Optional filter end date (ISO-8601 format)

        Returns:
            List of metadata dicts, sorted newest first

        Raises:
            FilterError: If limit or dates are invalid
            DynamoDBError: If query fails
        """

    @abstractmethod
    def check_duplicate_image(self, *, user_id: str, file_hash: str) -> bool:
        """Check whether an image already exists for a user.

        Args:
            user_id: Image owner
            file_hash: Hash of image content

        Returns:
            True if duplicate exists for this user, False otherwise

        Raises:
            DynamoDBError: If check fails
        """
