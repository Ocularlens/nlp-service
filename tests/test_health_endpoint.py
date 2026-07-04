"""Tests for the /health endpoint."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for the health check endpoint."""

    def test_health_returns_200(self, test_client: TestClient):
        """GET /health should return 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, test_client: TestClient):
        """GET /health should return the expected JSON structure."""
        response = test_client.get("/health")
        data = response.json()
        assert data == {"message": "Service is healthy!"}

    def test_health_has_request_id_header(self, test_client: TestClient):
        """GET /health response should include X-Request-ID header."""
        response = test_client.get("/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
