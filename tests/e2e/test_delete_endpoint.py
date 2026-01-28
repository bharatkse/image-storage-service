"""
E2E Tests for Delete Endpoint: DELETE /v1/images/{imageId}
"""


class TestDeleteEndpointSuccess:
    """E2E: Successful delete scenarios"""

    def test_delete_existing_image_returns_200(self, api_client, upload_valid_payload) -> None:
        """E2E: Delete existing image returns 200 OK"""
        # Upload
        upload_resp = api_client.post("/v1/images", upload_valid_payload)
        image_id = upload_resp.json()["image_id"]

        # Delete
        delete_resp = api_client.delete(f"/v1/images/{image_id}")

        assert delete_resp.status_code == 200
        body = delete_resp.json()
        assert "message" in body

    def test_delete_removes_from_list(self, api_client, upload_valid_payload) -> None:
        """E2E: Deleted image no longer appears in list"""
        user_id = "e2e-delete-user"

        # Upload
        payload = upload_valid_payload.copy()
        payload["user_id"] = user_id
        upload_resp = api_client.post("/v1/images", payload)
        image_id = upload_resp.json()["image_id"]

        # Verify in list
        list_resp = api_client.get("/v1/images", {"user_id": user_id})
        assert any(img["image_id"] == image_id for img in list_resp.json()["images"])

        # Delete
        delete_resp = api_client.delete(f"/v1/images/{image_id}")
        assert delete_resp.status_code == 200

        # Verify NOT in list
        list_resp_after = api_client.get("/v1/images", {"user_id": user_id})
        assert not any(img["image_id"] == image_id for img in list_resp_after.json()["images"])

    def test_delete_is_idempotent(self, api_client, upload_valid_payload) -> None:
        """E2E: Deleting twice returns error on second"""
        upload_resp = api_client.post("/v1/images", upload_valid_payload)
        image_id = upload_resp.json()["image_id"]

        # First delete
        delete_resp_1 = api_client.delete(f"/v1/images/{image_id}")
        assert delete_resp_1.status_code == 200

        # Second delete (should fail)
        delete_resp_2 = api_client.delete(f"/v1/images/{image_id}")
        assert delete_resp_2.status_code == 404


class TestDeleteEndpointNotFound:
    """E2E: 404 Not Found scenarios"""

    def test_delete_nonexistent_image_returns_404(self, api_client) -> None:
        """E2E: Delete non-existent image returns 404"""
        response = api_client.delete("/v1/images/fake-image-id-12345")

        assert response.status_code == 404
        body = response.json()
        assert "error" in body or "message" in body
