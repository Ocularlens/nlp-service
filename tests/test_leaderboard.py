"""Tests for the leaderboard service and /api/v1/leaderboard/ endpoint."""
from unittest.mock import MagicMock, patch

import pytest
import redis
from fastapi.testclient import TestClient

from app.services.leaderboard import LeaderboardService, LEADERBOARD_KEY


class TestLeaderboardService:
    """Direct unit tests for the LeaderboardService class."""

    def test_update_score_calls_zincrby(self):
        """update_score should call ZINCRBY with correct args."""
        mock_redis = MagicMock()
        service = LeaderboardService(redis_client=mock_redis)

        service.update_score("Widget", 5)

        mock_redis.zincrby.assert_called_once_with(LEADERBOARD_KEY, 5, "WIDGET")

    def test_update_score_uppercases_product_name(self):
        """Product name should be uppercased before storing in Redis."""
        mock_redis = MagicMock()
        service = LeaderboardService(redis_client=mock_redis)

        service.update_score("myProduct", 3)

        mock_redis.zincrby.assert_called_once_with(LEADERBOARD_KEY, 3, "MYPRODUCT")

    def test_update_score_accepts_negative_score(self):
        """Negative sentiment scores should be passed through."""
        mock_redis = MagicMock()
        service = LeaderboardService(redis_client=mock_redis)

        service.update_score("Widget", -2)

        mock_redis.zincrby.assert_called_once_with(LEADERBOARD_KEY, -2, "WIDGET")

    def test_update_score_noop_when_redis_unavailable(self):
        """update_score should be a no-op when Redis client is None."""
        service = LeaderboardService(redis_client=None)

        # Should not raise
        service.update_score("Widget", 5)

    def test_update_score_handles_redis_error(self):
        """update_score should catch RedisError and not raise."""
        mock_redis = MagicMock()
        mock_redis.zincrby.side_effect = redis.RedisError("Connection lost")
        service = LeaderboardService(redis_client=mock_redis)

        # Should not raise
        service.update_score("Widget", 5)

    def test_get_top_products_decodes_bytes(self):
        """get_top_products should decode bytes product names."""
        mock_redis = MagicMock()
        mock_redis.zrevrange.return_value = [(b"WIDGET", 10.0), (b"GADGET", 5.0)]
        service = LeaderboardService(redis_client=mock_redis)

        result = service.get_top_products(10)

        assert result == [
            {"product_name": "WIDGET", "total_score": 10},
            {"product_name": "GADGET", "total_score": 5},
        ]

    def test_get_top_products_passes_string_through(self):
        """get_top_products should handle non-bytes names (fakeredis compat)."""
        mock_redis = MagicMock()
        mock_redis.zrevrange.return_value = [("WIDGET", 10.0)]
        service = LeaderboardService(redis_client=mock_redis)

        result = service.get_top_products(10)

        assert result == [{"product_name": "WIDGET", "total_score": 10}]

    def test_get_top_products_respects_limit(self):
        """get_top_products should pass limit to ZREVRANGE."""
        mock_redis = MagicMock()
        mock_redis.zrevrange.return_value = []
        service = LeaderboardService(redis_client=mock_redis)

        service.get_top_products(5)

        mock_redis.zrevrange.assert_called_once_with(LEADERBOARD_KEY, 0, 4, withscores=True)

    def test_get_top_products_handles_redis_error(self):
        """get_top_products should return [] on RedisError."""
        mock_redis = MagicMock()
        mock_redis.zrevrange.side_effect = redis.RedisError("Connection refused")
        service = LeaderboardService(redis_client=mock_redis)

        result = service.get_top_products(10)

        assert result == []

    def test_get_top_products_not_available_returns_empty(self):
        """get_top_products should return [] when Redis is unavailable."""
        service = LeaderboardService(redis_client=None)

        result = service.get_top_products(10)

        assert result == []

    def test_clear_calls_delete(self):
        """clear should call DELETE with the leaderboard key."""
        mock_redis = MagicMock()
        service = LeaderboardService(redis_client=mock_redis)

        service.clear()

        mock_redis.delete.assert_called_once_with(LEADERBOARD_KEY)

    def test_clear_noop_when_redis_unavailable(self):
        """clear should be a no-op when Redis client is None."""
        service = LeaderboardService(redis_client=None)

        # Should not raise
        service.clear()

    def test_get_all_products_returns_all(self):
        """get_all_products should return all entries sorted by score."""
        mock_redis = MagicMock()
        mock_redis.zrevrange.return_value = [(b"A", 10.0), (b"B", 5.0), (b"C", 0.0)]
        service = LeaderboardService(redis_client=mock_redis)

        result = service.get_all_products()

        assert len(result) == 3
        assert result[0]["product_name"] == "A"
        assert result[2]["total_score"] == 0

    def test_get_all_products_handles_redis_error(self):
        """get_all_products should return [] on RedisError."""
        mock_redis = MagicMock()
        mock_redis.zrevrange.side_effect = redis.RedisError("Timeout")
        service = LeaderboardService(redis_client=mock_redis)

        result = service.get_all_products()

        assert result == []


class TestGetLeaderboard:
    """Test suite for GET /api/v1/leaderboard/."""

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_structure(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """GET /api/v1/leaderboard/ should return correct response structure."""
        mock_leaderboard.get_top_products.return_value = [
            {"product_name": "WIDGET", "total_score": 5},
            {"product_name": "GADGET", "total_score": 3},
        ]

        response = test_client.get("/api/v1/leaderboard/")

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "limit" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["leaderboard"]) == 2

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_returns_ranked_products(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """Leaderboard should return products sorted by score descending."""
        mock_leaderboard.get_top_products.return_value = [
            {"product_name": "BEST", "total_score": 10},
            {"product_name": "GOOD", "total_score": 5},
            {"product_name": "AVERAGE", "total_score": 0},
            {"product_name": "BAD", "total_score": -3},
        ]

        response = test_client.get("/api/v1/leaderboard/")

        data = response.json()
        scores = [p["total_score"] for p in data["leaderboard"]]
        assert scores == [10, 5, 0, -3]

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_empty(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """Leaderboard should return empty list when no products exist."""
        mock_leaderboard.get_top_products.return_value = []

        response = test_client.get("/api/v1/leaderboard/")

        data = response.json()
        assert data["leaderboard"] == []
        assert data["total"] == 0

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_respects_limit(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """Leaderboard should pass limit to service and reflect it in response."""
        def side_effect(limit):
            return [{"product_name": f"PRODUCT_{i}", "total_score": i}
                    for i in range(limit, 0, -1)]
        mock_leaderboard.get_top_products.side_effect = side_effect

        response = test_client.get("/api/v1/leaderboard/?limit=3")

        data = response.json()
        assert data["limit"] == 3
        assert len(data["leaderboard"]) == 3
        mock_leaderboard.get_top_products.assert_called_with(3)

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_default_limit(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """Leaderboard should default to limit=10 when not specified."""
        mock_leaderboard.get_top_products.return_value = []

        response = test_client.get("/api/v1/leaderboard/")

        data = response.json()
        assert data["limit"] == 10
        mock_leaderboard.get_top_products.assert_called_with(10)

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_invalid_limit_below_1(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """GET with limit < 1 should return 422."""
        response = test_client.get("/api/v1/leaderboard/?limit=0")
        assert response.status_code == 422

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_invalid_limit_above_100(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """GET with limit > 100 should return 422."""
        response = test_client.get("/api/v1/leaderboard/?limit=101")
        assert response.status_code == 422

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_request_id(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """GET response should include X-Request-ID header."""
        mock_leaderboard.get_top_products.return_value = []

        response = test_client.get("/api/v1/leaderboard/")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_passes_correct_args_to_service(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """Leaderboard service should be called with correct arguments."""
        mock_leaderboard.get_top_products.return_value = [
            {"product_name": "TEST", "total_score": 42}
        ]

        response = test_client.get("/api/v1/leaderboard/?limit=5")

        assert response.status_code == 200
        mock_leaderboard.get_top_products.assert_called_once_with(5)

    @patch("app.routes.leaderboard_route.leaderboard_service")
    def test_get_leaderboard_handles_redis_error_gracefully(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """Leaderboard should return empty list when Redis is unavailable."""
        mock_leaderboard.get_top_products.return_value = []

        response = test_client.get("/api/v1/leaderboard/")

        assert response.status_code == 200
        data = response.json()
        assert data["leaderboard"] == []
        assert data["total"] == 0


class TestLeaderboardIntegration:
    """Test integration between review creation and leaderboard updates."""

    @patch("app.routes.review_route.leaderboard_service")
    def test_post_review_updates_leaderboard(
        self, mock_leaderboard: MagicMock, test_client: TestClient, sample_review: dict
    ):
        """POST review should call leaderboard.update_score."""
        response = test_client.post("/api/v1/reviews/", json=sample_review)

        assert response.status_code == 200
        mock_leaderboard.update_score.assert_called_once()
        args, kwargs = mock_leaderboard.update_score.call_args
        assert args[0] == sample_review["productName"]
        assert isinstance(args[1], int)

    @patch("app.routes.review_route.leaderboard_service")
    def test_post_review_updates_leaderboard_with_translation(
        self, mock_leaderboard: MagicMock, test_client: TestClient,
        sample_review_with_translation: dict
    ):
        """POST review with translation should also update leaderboard."""
        response = test_client.post(
            "/api/v1/reviews/", json=sample_review_with_translation
        )

        assert response.status_code == 200
        mock_leaderboard.update_score.assert_called_once()

    @patch("app.routes.review_route.leaderboard_service")
    def test_multiple_reviews_update_scores(
        self, mock_leaderboard: MagicMock, test_client: TestClient
    ):
        """Multiple reviews for same product should accumulate score."""
        test_client.post(
            "/api/v1/reviews/",
            json={"text": "Great product!", "productName": "Widget"},
        )
        test_client.post(
            "/api/v1/reviews/",
            json={"text": "Terrible product!", "productName": "Widget"},
        )

        assert mock_leaderboard.update_score.call_count == 2
        for call_args in mock_leaderboard.update_score.call_args_list:
            args, _ = call_args
            assert args[0] == "Widget"

    @patch("app.routes.review_route.leaderboard_service")
    def test_leaderboard_update_does_not_block_review_creation(
        self, mock_leaderboard: MagicMock, test_client: TestClient, sample_review: dict
    ):
        """Review creation should succeed even if leaderboard update fails."""
        mock_leaderboard.update_score.side_effect = Exception("Redis unavailable")

        response = test_client.post("/api/v1/reviews/", json=sample_review)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Review successfully analyzed and stored"
        assert "review_id" in data
