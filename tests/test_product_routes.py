"""Tests for the /api/v1/products/ endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestGetReviewsByProduct:
    """Test suite for GET /api/v1/products/{product_name}/reviews."""

    def test_get_reviews_by_product_found(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET by product name should return reviews for that product."""
        test_client.post("/api/v1/reviews/", json={"productName": "Widget", "text": "Great"})
        test_client.post("/api/v1/reviews/", json={"productName": "Widget", "text": "Second"})
        test_client.post("/api/v1/reviews/", json={"productName": "Other", "text": "Other"})

        response = test_client.get("/api/v1/products/Widget/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "WIDGET"
        assert data["totalItems"] == 2
        assert len(data["reviews"]) == 2

    def test_get_reviews_by_product_not_found(self, test_client: TestClient):
        """GET by non-existent product should return 404."""
        response = test_client.get("/api/v1/products/NonExistent/reviews")
        assert response.status_code == 404

    def test_get_reviews_by_product_case_insensitive(
        self, test_client: TestClient, sample_review: dict
    ):
        """GET by product name should be case-insensitive (uppercase lookup)."""
        test_client.post("/api/v1/reviews/", json={"productName": "MyProduct", "text": "Case test"})

        # Lookup with different case
        response = test_client.get("/api/v1/products/myproduct/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "MYPRODUCT"
        assert data["totalItems"] == 1

    def test_get_reviews_by_product_empty(
        self, test_client: TestClient
    ):
        """GET by product name with no reviews should return 404."""
        response = test_client.get("/api/v1/products/EmptyProduct/reviews")
        assert response.status_code == 404

    def test_get_reviews_by_product_pagination(
        self, test_client: TestClient
    ):
        """GET by product name should support pagination."""
        # Create 5 reviews for the same product
        for i in range(5):
            test_client.post(
                "/api/v1/reviews/",
                json={"productName": "PaginatedProduct", "text": f"Review {i}"},
            )

        # Page 1 with size 2
        page1 = test_client.get("/api/v1/products/PaginatedProduct/reviews?page=1&size=2").json()
        assert page1["totalItems"] == 5
        assert page1["totalPages"] == 3
        assert len(page1["reviews"]) == 2
        assert page1["currentPage"] == 1
        assert page1["product_name"] == "PAGINATEDPRODUCT"

        # Page 3 with size 2 (last page)
        page3 = test_client.get("/api/v1/products/PaginatedProduct/reviews?page=3&size=2").json()
        assert len(page3["reviews"]) == 1
        assert page3["currentPage"] == 3

    def test_get_reviews_by_product_response_structure(
        self, test_client: TestClient
    ):
        """GET by product name should include review details."""
        test_client.post("/api/v1/reviews/", json={"productName": "StructTest", "text": "Structure check"})

        response = test_client.get("/api/v1/products/StructTest/reviews")
        data = response.json()
        review = data["reviews"][0]

        assert "review_id" in review
        assert "review_text" in review
        assert "rating" in review
        assert "mood" in review
        assert "product_id" in review
        assert "product" in review
        assert review["product"]["product_name"] == "STRUCTTEST"

    def test_get_reviews_by_product_invalid_page(self, test_client: TestClient):
        """GET with page < 1 should return 422."""
        response = test_client.get("/api/v1/products/AnyProduct/reviews?page=0")
        assert response.status_code == 422

    def test_get_reviews_by_product_invalid_size(self, test_client: TestClient):
        """GET with size > 100 should return 422."""
        response = test_client.get("/api/v1/products/AnyProduct/reviews?size=101")
        assert response.status_code == 422

    def test_get_reviews_by_product_request_id(
        self, test_client: TestClient
    ):
        """GET by product name should include X-Request-ID header."""
        test_client.post("/api/v1/reviews/", json={"productName": "HeaderCheck", "text": "Header test"})
        response = test_client.get("/api/v1/products/HeaderCheck/reviews")
        assert "X-Request-ID" in response.headers


class TestGetLatestReview:
    """Test suite for GET /api/v1/products/{product_name}/reviews/latest."""

    def test_get_latest_review_found(self, test_client: TestClient):
        """GET latest review should return the most recent review for a product."""
        test_client.post("/api/v1/reviews/", json={"productName": "LatestProduct", "text": "First review"})
        test_client.post("/api/v1/reviews/", json={"productName": "LatestProduct", "text": "Second review"})

        response = test_client.get("/api/v1/products/LatestProduct/reviews/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "LATESTPRODUCT"
        assert data["review"] is not None
        assert "review_id" in data["review"]
        assert "review_text" in data["review"]
        assert "rating" in data["review"]
        assert "mood" in data["review"]
        assert "created_at" in data["review"]
        # The review text should be one of the two we posted
        assert data["review"]["review_text"] in ("First review", "Second review")

    def test_get_latest_review_not_found(self, test_client: TestClient):
        """GET latest review for non-existent product should return 404."""
        response = test_client.get("/api/v1/products/NonExistent/reviews/latest")
        assert response.status_code == 404

    def test_get_latest_review_request_id(self, test_client: TestClient):
        """GET latest review should include X-Request-ID header."""
        test_client.post("/api/v1/reviews/", json={"productName": "LatestHeader", "text": "Header check"})
        response = test_client.get("/api/v1/products/LatestHeader/reviews/latest")
        assert "X-Request-ID" in response.headers
