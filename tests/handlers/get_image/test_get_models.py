"""Unit tests for get handler."""

import pytest
from handlers.get_image.models import GetImageRequest
from pydantic import ValidationError


class TestGetModels:
    """Test get request validation."""

    def test_valid_get_request(self) -> None:
        data = {"image_id": "img_abc123", "metadata": True}
        request = GetImageRequest(**data)
        assert request.image_id == "img_abc123"
        assert request.metadata is True

    def test_get_request_default_metadata(self) -> None:
        data = {"image_id": "img_abc123"}
        request = GetImageRequest(**data)
        assert request.image_id == "img_abc123"
        assert request.metadata is False

    def test_missing_image_id(self) -> None:
        data = {"metadata": True}
        with pytest.raises(ValidationError):
            GetImageRequest(**data)

    def test_empty_image_id(self) -> None:
        data = {"image_id": "", "metadata": True}

        with pytest.raises(ValidationError):
            GetImageRequest(**data)

    def test_whitespace_image_id_rejected(self) -> None:
        data = {"image_id": "   ", "metadata": True}

        # Fails min_length AFTER stripping (if added later)
        with pytest.raises(ValidationError):
            GetImageRequest(**data)

    def test_metadata_invalid_type_string(self) -> None:
        data = {"image_id": "img_123", "metadata": "yes"}

        with pytest.raises(ValidationError):
            GetImageRequest(**data)

    def test_metadata_none_rejected(self) -> None:
        data = {"image_id": "img_123", "metadata": None}

        with pytest.raises(ValidationError):
            GetImageRequest(**data)
