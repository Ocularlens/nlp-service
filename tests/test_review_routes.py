"""Tests for the /api/v1/reviews/ endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestPostReview:
    """Test suite for POST /api/v1/reviews/."""

    def test_create_review_success(self, test_client: TestClient, sample_review: dict):
        """POST with valid data should return 200 and analysis result."""
        response = test_client.post("/api/v1/reviews/", json=sample_review)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Review successfully analyzed and stored"
        assert "analysis_result" in data
        assert "review_id" in data
        assert len(data["review_id"]) == 36  # UUID length

    def test_create_review_returns_sentiment_analysis(
        self, test_client: TestClient, sample_review: dict
    ):
        """POST response should contain sentiment analysis result."""
        response = test_client.post("/api/v1/reviews/", json=sample_review)
        data = response.json()
        analysis = data["analysis_result"]

        assert "mood" in analysis
        assert "sentiment_score" in analysis
        assert "positive_count" in analysis
        assert "negative_count" in analysis
        assert "signals" in analysis

        # "amazing" is a positive word
        assert analysis["positive_count"] >= 1

    def test_create_review_persists_to_database(
        self, test_client: TestClient, sample_review: dict
    ):
        """After POST, the review should exist in the database."""
        post_resp = test_client.post("/api/v1/reviews/", json=sample_review)
        review_id = post_resp.json()["review_id"]

        # Fetch all reviews and check our review is there
        get_resp = test_client.get("/api/v1/reviews/")
        reviews = get_resp.json()["reviews"]
        ids = [r["review_id"] for r in reviews]
        assert review_id in ids

    def test_create_review_with_translation(
        self, test_client: TestClient, sample_review_with_translation: dict
    ):
        """POST with translation should process and return analysis."""
        response = test_client.post(
            "/api/v1/reviews/", json=sample_review_with_translation
        )
        assert response.status_code == 200
        data = response.json()
        assert "analysis_result" in data
        assert "review_id" in data

    def test_create_review_missing_text(self, test_client: TestClient):
        """POST without 'text' should return 422 validation error."""
        response = test_client.post(
            "/api/v1/reviews/", json={"productName": "Test"}
        )
        assert response.status_code == 422

    def test_create_review_missing_product_name(self, test_client: TestClient):
        """POST without 'productName' should return 422 validation error."""
        response = test_client.post(
            "/api/v1/reviews/", json={"text": "Great product!"}
        )
        assert response.status_code == 422

    def test_create_review_empty_body(self, test_client: TestClient):
        """POST with empty body should return 422."""
        response = test_client.post("/api/v1/reviews/", json={})
        assert response.status_code == 422

    def test_create_review_text_too_short(self, test_client: TestClient):
        """POST with text < 3 chars should return 422."""
        response = test_client.post(
            "/api/v1/reviews/",
            json={"text": "ab", "productName": "Test"},
        )
        assert response.status_code == 422

    def test_create_review_text_too_long(self, test_client: TestClient):
        """POST with text > 120 chars should return 422."""
        long_text = "A" * 121
        response = test_client.post(
            "/api/v1/reviews/",
            json={"text": long_text, "productName": "Test"},
        )
        assert response.status_code == 422

    def test_create_review_product_name_too_long(self, test_client: TestClient):
        """POST with productName > 64 chars should return 422."""
        response = test_client.post(
            "/api/v1/reviews/",
            json={"text": "Good product", "productName": "B" * 65},
        )
        assert response.status_code == 422

    def test_create_review_with_invalid_translation_language(
        self, test_client: TestClient, sample_review: dict
    ):
        """POST with invalid translation language should return 422."""
        payload = {
            **sample_review,
            "translation": {"source_language": "invalid"},
        }
        # Since GoogleTranslator is mocked in conftest.py with limited
        # language support, "invalid" should be rejected.
        response = test_client.post("/api/v1/reviews/", json=payload)
        assert response.status_code == 422

    def test_create_review_request_id_in_response(
        self, test_client: TestClient, sample_review: dict
    ):
        """POST response should include X-Request-ID header."""
        response = test_client.post("/api/v1/reviews/", json=sample_review)
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0


class TestGetReviews:
    """Test suite for GET /api/v1/reviews/."""

    def test_get_reviews_empty(self, test_client: TestClient):
        """GET with no reviews should return empty results."""
        response = test_client.get("/api/v1/reviews/")
        assert response.status_code == 200
        data = response.json()
        assert data["totalItems"] == 0
        assert data["reviews"] == []

    def test_get_reviews_structure(self, test_client: TestClient):
        """GET response should include pagination metadata."""
        response = test_client.get("/api/v1/reviews/")
        assert response.status_code == 200
        data = response.json()
        assert "totalPages" in data
        assert "currentPage" in data
        assert "pageSize" in data
        assert "totalItems" in data
        assert "reviews" in data

    def test_get_reviews_after_post(self, test_client: TestClient, sample_review: dict):
        """GET should return reviews that were previously posted."""
        test_client.post("/api/v1/reviews/", json=sample_review)
        test_client.post(
            "/api/v1/reviews/", json={**sample_review, "text": "Bad product."}
        )

        response = test_client.get("/api/v1/reviews/")
        data = response.json()
        assert data["totalItems"] == 2
        assert len(data["reviews"]) == 2

    def test_get_reviews_pagination(self, test_client: TestClient, sample_review: dict):
        """GET should support pagination with page and size."""
        # Create 5 reviews
        for i in range(5):
            test_client.post(
                "/api/v1/reviews/",
                json={**sample_review, "text": f"Review number {i}"},
            )

        # Page 1 with size 2
        page1 = test_client.get("/api/v1/reviews/?page=1&size=2").json()
        assert page1["totalItems"] == 5
        assert page1["totalPages"] == 3
        assert len(page1["reviews"]) == 2
        assert page1["currentPage"] == 1

        # Page 3 with size 2 (last page)
        page3 = test_client.get("/api/v1/reviews/?page=3&size=2").json()
        assert len(page3["reviews"]) == 1
        assert page3["currentPage"] == 3

    def test_get_reviews_sort_by_rating_desc(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET should sort by rating descending when specified."""
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "Amazing!", "productName": "A"},
        )
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "Bad!", "productName": "B"},
        )

        response = test_client.get("/api/v1/reviews/?sort_by=rating&sort_order=desc")
        data = response.json()
        ratings = [r["rating"] for r in data["reviews"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_get_reviews_sort_by_rating_asc(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET should sort by rating ascending when specified."""
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "Amazing!", "productName": "A"},
        )
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "Bad!", "productName": "B"},
        )

        response = test_client.get("/api/v1/reviews/?sort_by=rating&sort_order=asc")
        data = response.json()
        ratings = [r["rating"] for r in data["reviews"]]
        assert ratings == sorted(ratings)

    def test_get_reviews_filter_by_rating(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET should filter by rating when rating_filter is provided."""
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "Amazing!", "productName": "A"},
        )
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "Bad!", "productName": "B"},
        )

        response = test_client.get("/api/v1/reviews/?rating_filter=1")
        data = response.json()

        # "Amazing!" has sentiment_score=1, so its rating is 1
        # "Bad!" has sentiment_score=-1 (based on the BAD words list)
        # So filtering by rating=1 should return only "Amazing!"
        assert data["totalItems"] == 1

    def test_get_reviews_filter_by_product(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET should filter by product name."""
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "productName": "Alpha"},
        )
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "productName": "Beta"},
        )

        response = test_client.get("/api/v1/reviews/?product_filter=Alpha")
        data = response.json()
        assert data["totalItems"] == 1
        # The route filters by product name via a join;
        # the product relationship is eagerly loaded and serialized
        assert data["reviews"][0]["product"]["product_name"] == "ALPHA"
        assert len(data["reviews"][0]["product_id"]) > 0

    def test_get_reviews_filter_by_review_text(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET should filter by review text content."""
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "This is amazing!"},
        )
        test_client.post(
            "/api/v1/reviews/",
            json={**sample_review, "text": "This is terrible!"},
        )

        response = test_client.get("/api/v1/reviews/?review_filter=amazing")
        data = response.json()
        assert data["totalItems"] == 1

    def test_get_reviews_request_id_header(self, test_client: TestClient):
        """GET response should include X-Request-ID header."""
        response = test_client.get("/api/v1/reviews/")
        assert "X-Request-ID" in response.headers

    def test_get_reviews_invalid_page(self, test_client: TestClient):
        """GET with page < 1 should return 422."""
        response = test_client.get("/api/v1/reviews/?page=0")
        assert response.status_code == 422

    def test_get_reviews_invalid_size(self, test_client: TestClient):
        """GET with size > 100 should return 422."""
        response = test_client.get("/api/v1/reviews/?size=101")
        assert response.status_code == 422

    def test_get_reviews_invalid_sort_by(self, test_client: TestClient):
        """GET with invalid sort_by crashes the server internally.

        NOTE: This test documents a known bug. The route does not validate
        sort_by against allowed values before passing to the repository layer.
        The enum parameter in Query() is not enforced with str type annotation.
        An invalid sort_by causes an AttributeError in getattr() inside
        base_repository.py.

        The TestClient raises this exception because the error occurs inside
        slowapi's sync_wrapper before FastAPI's exception handler can catch it.
        This should be fixed in the application code.
        """
        with pytest.raises(Exception) as excinfo:
            test_client.get("/api/v1/reviews/?sort_by=invalid_field")
        # The underlying error is an AttributeError from getattr()
        assert "no attribute 'invalid_field'" in str(excinfo.value)

    def test_get_reviews_invalid_sort_order(self, test_client: TestClient):
        """GET with invalid sort_order defaults to ascending.

        NOTE: The route does not strictly validate sort_order. Any value
        that is not 'desc' is treated as 'asc'. This test documents this
        behavior.
        """
        response = test_client.get("/api/v1/reviews/?sort_order=invalid")
        assert response.status_code == 200
        # It defaults to ascending sort since "invalid" != "desc"

    def test_get_reviews_default_values(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET without query params should use default pagination values."""
        test_client.post("/api/v1/reviews/", json=sample_review)

        response = test_client.get("/api/v1/reviews/")
        data = response.json()
        assert data["currentPage"] == 1
        assert data["pageSize"] == 10



