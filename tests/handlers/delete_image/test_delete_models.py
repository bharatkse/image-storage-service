"""Unit tests for delete handler models."""

import pytest
from handlers.delete_image.models import DeleteImageRequest
from pydantic import ValidationError


class TestDeleteModels:
    """Test delete request validation."""

    def test_valid_delete_request(self) -> None:
        data: dict[str, str] = {"image_id": "img_abc123"}

        request = DeleteImageRequest(**data)

        assert request.image_id == "img_abc123"

    def test_missing_image_id(self) -> None:
        data: dict[str, str] = {}

        with pytest.raises(ValidationError):
            DeleteImageRequest(**data)

    def test_empty_image_id(self) -> None:
        data: dict[str, str] = {"image_id": ""}

        with pytest.raises(ValidationError):
            DeleteImageRequest(**data)

    def test_whitespace_image_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DeleteImageRequest(image_id="   ")
