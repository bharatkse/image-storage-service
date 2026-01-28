"""
E2E Tests for HTTP Error Responses
"""


class TestErrorResponses:
    """E2E: Verify error response formats"""

    def test_400_error_has_message(self, api_client) -> None:
        """E2E: 400 errors include error message"""
        response = api_client.post("/v1/images", {})

        assert response.status_code == 400
        body = response.json()
        assert "error" in body or "message" in body

    def test_404_error_has_message(self, api_client) -> None:
        """E2E: 404 errors include error message"""
        response = api_client.get("/v1/images/fake-id")

        assert response.status_code == 404
        body = response.json()
        assert "error" in body or "message" in body

    def test_error_response_is_json(self, api_client) -> None:
        """E2E: Error responses are valid JSON"""
        response = api_client.post("/v1/images", {})

        assert response.status_code == 400
        # Should not raise JSONDecodeError
        body = response.json()
        assert isinstance(body, dict)
