"""
E2E Tests for Upload Endpoint: POST /v1/images
"""

import base64

from core.utils.constants import MAX_FILE_SIZE

# 1x1 pixel PNG (minimal valid image)
SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/" "wlseKgAAAABJRU5ErkJggg=="
)

EMPTY_BASE64 = base64.b64encode(b"").decode()
OVERSIZED_BASE64 = base64.b64encode(b"A" * (MAX_FILE_SIZE + 1)).decode()

UPLOAD_MINIMAL_PAYLOAD = {
    "user_id": "test-user-minimal",
    "image_name": "minimal.png",
    "file": SAMPLE_PNG_BASE64,
}

UPLOAD_WITH_SPECIAL_CHARS = {
    "user_id": "test-user-special",
    "image_name": "photo_2024-01-26_final-copy.jpg",
    "description": "Image with special characters: !@#$% and more",
    "tags": ["special-tag", "test_tag", "tag.with.dots"],
    "file": SAMPLE_PNG_BASE64,
}

UPLOAD_WITH_LONG_DESCRIPTION = {
    "user_id": "test-user-long-desc",
    "image_name": "long-desc.jpg",
    "description": "A" * 1000,  # max allowed
    "tags": ["long", "description"],
    "file": SAMPLE_PNG_BASE64,
}

UPLOAD_MISSING_USER_ID = {"image_name": "test.jpg", "file": SAMPLE_PNG_BASE64}
UPLOAD_MISSING_IMAGE_NAME = {"user_id": "test-user", "file": SAMPLE_PNG_BASE64}
UPLOAD_MISSING_FILE = {"user_id": "test-user", "image_name": "test.jpg"}
UPLOAD_INVALID_BASE64 = {"user_id": "test-user", "image_name": "test.jpg", "file": "not-valid-base64"}


class TestUploadEndpointSuccess:
    """E2E: Successful upload scenarios"""

    def test_upload_valid_payload_returns_201(self, api_client, upload_valid_payload) -> None:
        """E2E: Upload with all fields returns 201 Created"""
        response = api_client.post("/v1/images", upload_valid_payload)

        assert response.status_code == 201
        body = response.json()
        assert body["image_id"]
        assert body["user_id"] == upload_valid_payload["user_id"]
        assert body["image_name"] == upload_valid_payload["image_name"]
        assert body["description"] == upload_valid_payload["description"]
        assert body["message"] == "Image uploaded successfully"

    def test_upload_minimal_payload_returns_201(self, api_client) -> None:
        """E2E: Upload with minimal fields returns 201"""
        response = api_client.post("/v1/images", UPLOAD_MINIMAL_PAYLOAD)

        assert response.status_code == 201
        assert response.json()["image_id"]

    def test_upload_response_includes_created_at(self, api_client, upload_valid_payload) -> None:
        """Response includes ISO-8601 created_at timestamp."""
        response = api_client.post("/v1/images", upload_valid_payload)
        assert "T" in response.json()["created_at"]

    def test_upload_response_includes_s3_key(self, api_client, upload_valid_payload) -> None:
        """Response includes user-scoped S3 key."""
        response = api_client.post("/v1/images", upload_valid_payload)
        assert response.json()["s3_key"].startswith(f"images/{upload_valid_payload['user_id']}/")

    def test_upload_tags_as_comma_separated_string(self, api_client, upload_valid_payload) -> None:
        """Comma-separated tags string is accepted."""
        payload = upload_valid_payload.copy()
        payload["tags"] = "tag1, tag2, tag3"
        assert api_client.post("/v1/images", payload).status_code == 201

    def test_upload_with_special_characters(self, api_client) -> None:
        """Special characters in metadata are allowed."""
        assert api_client.post("/v1/images", UPLOAD_WITH_SPECIAL_CHARS).status_code == 201

    def test_upload_with_max_description_length(self, api_client) -> None:
        """Description at max allowed length succeeds."""
        assert api_client.post("/v1/images", UPLOAD_WITH_LONG_DESCRIPTION).status_code == 201


class TestUploadEndpointValidation:
    """E2E: Validation failure scenarios"""

    def test_missing_user_id_returns_400(self, api_client) -> None:
        """Missing user_id returns 400."""
        assert api_client.post("/v1/images", UPLOAD_MISSING_USER_ID).status_code == 400

    def test_missing_image_name_returns_400(self, api_client) -> None:
        """Missing image_name returns 400."""
        assert api_client.post("/v1/images", UPLOAD_MISSING_IMAGE_NAME).status_code == 400

    def test_missing_file_returns_400(self, api_client) -> None:
        """Missing file returns 400."""
        assert api_client.post("/v1/images", UPLOAD_MISSING_FILE).status_code == 400

    def test_invalid_base64_returns_400(self, api_client) -> None:
        """Invalid base64 string returns 400."""
        assert api_client.post("/v1/images", UPLOAD_INVALID_BASE64).status_code == 400

    def test_empty_file_string_returns_400(self, api_client, upload_valid_payload) -> None:
        """Whitespace-only file string returns 400."""
        payload = upload_valid_payload.copy()
        payload["file"] = "   "
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_empty_decoded_file_returns_400(self, api_client, upload_valid_payload) -> None:
        """Base64-decoded empty file returns 400."""
        payload = upload_valid_payload.copy()
        payload["file"] = EMPTY_BASE64
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_file_size_exceeds_limit_returns_400(self, api_client, upload_valid_payload) -> None:
        """File larger than MAX_FILE_SIZE returns 400."""
        payload = upload_valid_payload.copy()
        payload["file"] = OVERSIZED_BASE64
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_invalid_image_extension_returns_400(self, api_client, upload_valid_payload) -> None:
        """Invalid image extension returns 400."""
        payload = upload_valid_payload.copy()
        payload["image_name"] = "file.exe"
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_image_name_without_extension_returns_400(self, api_client, upload_valid_payload) -> None:
        """Image name without extension returns 400."""
        payload = upload_valid_payload.copy()
        payload["image_name"] = "image"
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_user_id_too_short_returns_400(self, api_client, upload_valid_payload) -> None:
        """user_id shorter than minimum length returns 400."""
        payload = upload_valid_payload.copy()
        payload["user_id"] = "ab"
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_user_id_too_long_returns_400(self, api_client, upload_valid_payload) -> None:
        """user_id longer than maximum length returns 400."""
        payload = upload_valid_payload.copy()
        payload["user_id"] = "a" * 51
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_invalid_user_id_pattern_returns_400(self, api_client, upload_valid_payload) -> None:
        """Invalid user_id pattern returns 400."""
        payload = upload_valid_payload.copy()
        payload["user_id"] = "invalid user!"
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_more_than_10_tags_returns_400(self, api_client, upload_valid_payload) -> None:
        """More than 10 tags returns 400."""
        payload = upload_valid_payload.copy()
        payload["tags"] = [f"tag-{i}" for i in range(11)]
        assert api_client.post("/v1/images", payload).status_code == 400

    def test_invalid_tags_type_returns_400(self, api_client, upload_valid_payload) -> None:
        """Invalid tags type returns 400."""
        payload = upload_valid_payload.copy()
        payload["tags"] = {"tag": "invalid"}
        assert api_client.post("/v1/images", payload).status_code == 400


class TestUploadEndpointBehavior:
    """E2E: Behavioral guarantees"""

    def test_multiple_unique_uploads_generate_unique_ids(self, api_client, upload_valid_payload) -> None:
        """Uploading different valid images generates unique image_ids."""
        ids = set()

        for i in range(3):
            payload = upload_valid_payload.copy()
            payload["image_name"] = f"image-{i}.png"

            # Make image content unique but still a valid PNG
            unique_png_bytes = b"\x89PNG\r\n\x1a\n" + f"unique-{i}".encode()
            payload["file"] = base64.b64encode(unique_png_bytes).decode()

            response = api_client.post("/v1/images", payload)
            assert response.status_code == 201
            ids.add(response.json()["image_id"])

        assert len(ids) == 3
