"""
E2E Tests for List Endpoint: GET /v1/images
"""

import base64
from datetime import datetime, timedelta, timezone


def upload_images(
    api_client,
    *,
    user_id: str,
    base_payload: dict,
    count: int,
) -> list[str]:
    """Upload multiple unique images for a user and return their image_ids."""
    image_ids: list[str] = []

    for i in range(count):
        payload = base_payload.copy()
        payload["user_id"] = user_id
        payload["image_name"] = f"image-{i}.png"

        # Minimal valid PNG header + unique content
        unique_png = b"\x89PNG\r\n\x1a\n" + f"img-{i}".encode()
        payload["file"] = base64.b64encode(unique_png).decode()

        response = api_client.post("/v1/images", payload)
        assert response.status_code == 201, response.json()

        image_ids.append(response.json()["image_id"])

    return image_ids


class TestListEndpointSuccess:
    """E2E: Successful list scenarios"""

    def test_list_returns_200_with_valid_user_id(self, api_client) -> None:
        """Valid user_id returns expected response shape."""
        response = api_client.get("/v1/images", {"user_id": "test-user-123"})
        assert response.status_code == 200

        body = response.json()

        required_keys = {
            "images",
            "total_count",
            "returned_count",
            "pagination",
        }

        assert required_keys.issubset(body.keys())
        assert isinstance(body["images"], list)
        assert isinstance(body["total_count"], int)
        assert isinstance(body["returned_count"], int)

    def test_list_returns_empty_for_nonexistent_user(self, api_client) -> None:
        """Non-existent user returns empty result set."""
        response = api_client.get("/v1/images", {"user_id": "no-such-user"})
        assert response.status_code == 200

        body = response.json()
        assert body["images"] == []
        assert body["total_count"] == 0
        assert body["returned_count"] == 0
        assert body["pagination"]["has_more"] is False

    def test_list_includes_uploaded_images(self, api_client, upload_valid_payload) -> None:
        """Uploaded images appear in list response."""
        user_id = "e2e-list-user"

        payload = upload_valid_payload.copy()
        payload["user_id"] = user_id

        upload = api_client.post("/v1/images", payload)
        assert upload.status_code == 201

        response = api_client.get("/v1/images", {"user_id": user_id})
        assert response.status_code == 200

        body = response.json()
        assert body["total_count"] >= 1
        assert any(img["user_id"] == user_id for img in body["images"])

    def test_list_respects_limit_parameter(self, api_client) -> None:
        """Limit parameter restricts number of results."""
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "limit": 5},
        )
        assert response.status_code == 200

        body = response.json()
        assert body["pagination"]["limit"] == 5
        assert body["returned_count"] <= 5


class TestListEndpointFilters:
    """E2E: Filtering support"""

    def test_list_filters_by_name_contains(self, api_client, upload_valid_payload) -> None:
        """name_contains filters images by substring."""
        user_id = "e2e-filter-name"

        payload = upload_valid_payload.copy()
        payload["user_id"] = user_id
        payload["image_name"] = "holiday-photo.png"

        api_client.post("/v1/images", payload)

        response = api_client.get(
            "/v1/images",
            {"user_id": user_id, "name_contains": "holiday"},
        )
        assert response.status_code == 200

        images = response.json()["images"]
        assert all("holiday" in img["image_name"] for img in images)

    def test_list_filters_by_start_date(self, api_client, upload_valid_payload) -> None:
        """start_date filters images created after date."""
        user_id = "e2e-filter-start-date"

        payload = upload_valid_payload.copy()
        payload["user_id"] = user_id

        api_client.post("/v1/images", payload)

        today = datetime.now(timezone.utc).date().isoformat()

        response = api_client.get(
            "/v1/images",
            {"user_id": user_id, "start_date": today},
        )
        assert response.status_code == 200

    def test_list_filters_by_end_date(self, api_client, upload_valid_payload) -> None:
        """end_date filters images created before date."""
        user_id = "e2e-filter-end-date"

        payload = upload_valid_payload.copy()
        payload["user_id"] = user_id

        api_client.post("/v1/images", payload)

        today = datetime.now(timezone.utc).date().isoformat()

        response = api_client.get(
            "/v1/images",
            {"user_id": user_id, "end_date": today},
        )
        assert response.status_code == 200

    def test_list_filters_by_date_range(self, api_client, upload_valid_payload) -> None:
        """start_date and end_date together filter correctly."""
        user_id = "e2e-filter-date-range"

        payload = upload_valid_payload.copy()
        payload["user_id"] = user_id

        api_client.post("/v1/images", payload)

        today = datetime.now(timezone.utc).date()
        start = (today - timedelta(days=1)).isoformat()
        end = today.isoformat()

        response = api_client.get(
            "/v1/images",
            {
                "user_id": user_id,
                "start_date": start,
                "end_date": end,
            },
        )
        assert response.status_code == 200


class TestListEndpointOrdering:
    """E2E: Sorting behavior for list images endpoint"""

    def test_list_returns_newest_first(self, api_client, upload_valid_payload) -> None:
        """Images are returned in reverse chronological order by default."""
        user_id = "e2e-order-user-default"

        upload_images(
            api_client,
            user_id=user_id,
            base_payload=upload_valid_payload,
            count=3,
        )

        response = api_client.get("/v1/images", {"user_id": user_id})
        assert response.status_code == 200

        images = response.json()["images"]
        timestamps = [img["created_at"] for img in images]

        assert timestamps == sorted(timestamps, reverse=True)

    def test_sort_by_created_at_desc_default(self, api_client, upload_valid_payload) -> None:
        """Explicit default sort (created_at desc) returns newest first."""
        user_id = "e2e-order-user-desc"

        upload_images(
            api_client,
            user_id=user_id,
            base_payload=upload_valid_payload,
            count=3,
        )

        response = api_client.get("/v1/images", {"user_id": user_id})
        assert response.status_code == 200

        images = response.json()["images"]
        timestamps = [img["created_at"] for img in images]

        assert timestamps == sorted(timestamps, reverse=True)

    def test_sort_by_created_at_asc(self, api_client, upload_valid_payload) -> None:
        """Sorting by created_at ascending returns oldest first."""
        user_id = "e2e-order-user-asc"

        upload_images(
            api_client,
            user_id=user_id,
            base_payload=upload_valid_payload,
            count=3,
        )

        response = api_client.get(
            "/v1/images",
            {"user_id": user_id, "sort_order": "asc"},
        )
        assert response.status_code == 200

        images = response.json()["images"]
        timestamps = [img["created_at"] for img in images]

        assert timestamps == sorted(timestamps)

    def test_sort_by_image_name(self, api_client, upload_valid_payload) -> None:
        """Sorting by image_name orders images alphabetically."""
        user_id = "e2e-order-user-name"

        upload_images(
            api_client,
            user_id=user_id,
            base_payload=upload_valid_payload,
            count=3,
        )

        response = api_client.get(
            "/v1/images",
            {"user_id": user_id, "sort_by": "image_name"},
        )
        assert response.status_code == 200

        images = response.json()["images"]
        names = [img["image_name"] for img in images]

        assert names == sorted(names, reverse=True)


class TestListEndpointValidation:
    """E2E: Validation failures"""

    def test_missing_user_id_returns_400(self, api_client) -> None:
        """Missing user_id returns 400."""
        assert api_client.get("/v1/images", {}).status_code == 400

    def test_empty_user_id_returns_400(self, api_client) -> None:
        """Empty user_id returns 400."""
        assert api_client.get("/v1/images", {"user_id": ""}).status_code == 400

    def test_invalid_date_format_returns_400(self, api_client) -> None:
        """Invalid date format returns 400."""
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "start_date": "2024/01/01"},
        )
        assert response.status_code == 400

    def test_start_date_after_end_date_returns_400(self, api_client) -> None:
        """start_date later than end_date returns 400."""
        response = api_client.get(
            "/v1/images",
            {
                "user_id": "test-user",
                "start_date": "2025-01-10",
                "end_date": "2024-01-01",
            },
        )
        assert response.status_code == 400

    def test_limit_above_max_returns_400(self, api_client) -> None:
        """limit greater than maximum allowed returns 400."""
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "limit": 101},
        )
        assert response.status_code == 400

    def test_offset_negative_returns_400(self, api_client) -> None:
        """Negative offset value returns 400."""
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "offset": -1},
        )
        assert response.status_code == 400

    def test_invalid_sort_by_returns_400(self, api_client) -> None:
        """Invalid sort_by field returns 400."""
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "sort_by": "invalid"},
        )
        assert response.status_code == 400

    def test_invalid_sort_order_returns_400(self, api_client) -> None:
        """Invalid sort_order value returns 400."""
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "sort_order": "up"},
        )
        assert response.status_code == 400


class TestListPagination:
    """E2E: Pagination behavior"""

    def test_limit_is_respected(self, api_client) -> None:
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "limit": 5},
        )

        body = response.json()

        assert body["pagination"]["limit"] == 5
        assert body["returned_count"] <= 5

    def test_offset_is_respected(self, api_client) -> None:
        response = api_client.get(
            "/v1/images",
            {"user_id": "test-user", "offset": 5},
        )

        assert response.status_code == 200
        assert response.json()["pagination"]["offset"] == 5
