"""
E2E Tests for API Authentication
"""

import requests


class TestAPIKeyAuthentication:
    """E2E: x-api-key header validation"""

    def test_request_without_api_key_returns_403(self, api_details) -> None:
        """E2E: Request without x-api-key returns 403 Forbidden"""
        response = requests.post(
            f'{api_details["endpoint"]}/v1/images',
            json={"user_id": "test"},
            headers={"Content-Type": "application/json"},
            # Missing x-api-key
        )

        assert response.status_code == 403

    def test_request_with_invalid_api_key_returns_403(self, api_details) -> None:
        """E2E: Request with invalid x-api-key returns 403"""
        response = requests.post(
            f'{api_details["endpoint"]}/v1/images',
            json={"user_id": "test"},
            headers={"Content-Type": "application/json", "x-api-key": "invalid-key-xyz-123"},
        )

        assert response.status_code == 403

    def test_request_with_empty_api_key_returns_403(self, api_details) -> None:
        """E2E: Request with empty x-api-key returns 403"""
        response = requests.post(
            f'{api_details["endpoint"]}/v1/images',
            json={"user_id": "test"},
            headers={"Content-Type": "application/json", "x-api-key": ""},
        )

        assert response.status_code == 403
