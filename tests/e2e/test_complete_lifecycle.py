"""
E2E Tests for Complete User Lifecycle
Upload → List → Get → Delete → Verify
"""


class TestCompleteLifecycle:
    """E2E: Complete image lifecycle workflow"""

    def test_upload_list_get_delete_workflow(self, api_client, upload_valid_payload) -> None:
        """
        E2E: Complete workflow - Upload, List, Get, Delete

        This is the MOST IMPORTANT E2E test!
        Tests the entire user journey through the API.
        """
        user_id = "e2e-lifecycle-complete"
        image_name = "lifecycle-complete.jpg"

        # Step 1: Upload
        print("\n[1/5] Uploading image...")
        payload = upload_valid_payload.copy()
        payload["user_id"] = user_id
        payload["image_name"] = image_name

        upload_resp = api_client.post("/v1/images", payload)
        assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
        image_id = upload_resp.json()["image_id"]
        print(f"  Uploaded with image_id: {image_id}")

        #  Step 2: List - verify upload
        print("[2/5] Listing images...")
        list_resp = api_client.get("/v1/images", {"user_id": user_id})
        assert list_resp.status_code == 200
        images = list_resp.json()["images"]
        assert any(img["image_id"] == image_id for img in images)
        print(f"  Image found in list ({len(images)} total)")

        # Step 3: Get - download image
        print("[3/5] Getting/downloading image...")
        get_resp = api_client.get(f"/v1/images/{image_id}")
        assert get_resp.status_code == 200
        print(f"  Downloaded {len(get_resp.content)} bytes")

        # Step 4: Delete
        print("[4/5] Deleting image...")
        del_resp = api_client.delete(f"/v1/images/{image_id}")
        assert del_resp.status_code == 200
        print("  Image deleted")

        # Step 5: List - verify deletion
        print("[5/5] Verifying deletion...")
        list_resp_after = api_client.get("/v1/images", {"user_id": user_id})
        assert list_resp_after.status_code == 200
        images_after = list_resp_after.json()["images"]
        assert not any(img["image_id"] == image_id for img in images_after)
        print(f" Image removed from list ({len(images_after)} remaining)")

        print("\n Complete lifecycle workflow passed! \n")

    def test_multiple_users_isolated(self, api_client, upload_valid_payload) -> None:
        """E2E: Multiple users' images are isolated"""
        user1_id = "e2e-user-1"
        user2_id = "e2e-user-2"

        # Upload for user 1
        payload1 = upload_valid_payload.copy()
        payload1["user_id"] = user1_id
        resp1 = api_client.post("/v1/images", payload1)
        assert resp1.status_code == 201

        # Upload for user 2
        payload2 = upload_valid_payload.copy()
        payload2["user_id"] = user2_id
        resp2 = api_client.post("/v1/images", payload2)
        assert resp2.status_code == 201

        # User 1 should only see their images
        list_resp1 = api_client.get("/v1/images", {"user_id": user1_id})
        user1_images = list_resp1.json()["images"]
        assert all(img["user_id"] == user1_id for img in user1_images)

        # User 2 should only see their images
        list_resp2 = api_client.get("/v1/images", {"user_id": user2_id})
        user2_images = list_resp2.json()["images"]
        assert all(img["user_id"] == user2_id for img in user2_images)
