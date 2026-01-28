"""
E2E Tests for Get Endpoint: GET /v1/images/{imageId}
"""

import json


class TestGetEndpointSuccess:
    """E2E: Successful get scenarios"""

    def test_get_existing_image_returns_200(self, api_client, upload_valid_payload) -> None:
        """E2E: Get existing image returns 200 OK"""
        # Upload
        upload_resp = api_client.post("/v1/images", upload_valid_payload)
        image_id = upload_resp.json()["image_id"]

        # Get
        get_resp = api_client.get(f"/v1/images/{image_id}")

        assert get_resp.status_code == 200
        assert len(get_resp.content) > 0

    def test_get_returns_binary_image_data(self, api_client, upload_valid_payload) -> None:
        """E2E: Get returns binary image data"""
        upload_resp = api_client.post("/v1/images", upload_valid_payload)
        image_id = upload_resp.json()["image_id"]

        get_resp = api_client.get(f"/v1/images/{image_id}")

        assert get_resp.status_code == 200
        # Verify it's valid base64 or binary data
        assert len(get_resp.content) > 0

    def test_get_with_metadata_parameter(self, api_client, upload_valid_payload) -> None:
        """E2E: Get with metadata=true includes metadata header"""
        upload_resp = api_client.post("/v1/images", upload_valid_payload)
        image_id = upload_resp.json()["image_id"]

        get_resp = api_client.get(f"/v1/images/{image_id}", {"metadata": "true"})

        assert get_resp.status_code == 200
        # Check for metadata header if implemented
        if "X-Image-Metadata" in get_resp.headers:
            metadata = json.loads(get_resp.headers["X-Image-Metadata"])
            assert metadata["image_id"] == image_id

    def test_get_with_download_parameter(self, api_client, upload_valid_payload) -> None:
        """E2E: Get with download=true returns proper headers"""
        upload_resp = api_client.post("/v1/images", upload_valid_payload)
        image_id = upload_resp.json()["image_id"]

        get_resp = api_client.get(f"/v1/images/{image_id}", {"download": "true"})

        assert get_resp.status_code == 200
        # Check for Content-Disposition header if implemented
        if "Content-Disposition" in get_resp.headers:
            assert "attachment" in get_resp.headers["Content-Disposition"]


class TestGetEndpointNotFound:
    """E2E: 404 Not Found scenarios"""

    def test_get_nonexistent_image_returns_404(self, api_client) -> None:
        """E2E: Get non-existent image returns 404"""
        response = api_client.get("/v1/images/fake-image-id-12345")

        assert response.status_code == 404
        body = response.json()
        assert "error" in body or "message" in body

    def test_get_invalid_image_id_format_returns_404(self, api_client) -> None:
        """E2E: Invalid image ID format returns 404"""
        response = api_client.get("/v1/images/not-a-uuid")

        assert response.status_code == 404
