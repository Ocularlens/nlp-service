"""Tests for the ReviewRepository class."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infra.database import Base
from app.repository import ReviewRepository
from app.models import Review


@pytest.fixture
def repo_session():
    """Create a fresh SQLite session for each test with all tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def review_repo(repo_session):
    """Create a ReviewRepository bound to the test session."""
    return ReviewRepository(repo_session)


class TestReviewRepository:
    """Test suite for ReviewRepository CRUD operations."""

    def test_create_review(self, review_repo):
        """Creating a review should persist it and return it with a review_id."""
        review = review_repo.create(
            product="Test Product",
            review_text="This is a great product!",
            rating=2,
        )
        assert review.review_id is not None
        assert len(review.review_id) == 36  # UUID length
        assert review.product == "Test Product"
        assert review.review_text == "This is a great product!"
        assert review.rating == 2

    def test_create_generates_unique_ids(self, review_repo):
        """Each created review should get a unique review_id."""
        review1 = review_repo.create(
            product="Product A", review_text="Good", rating=1
        )
        review2 = review_repo.create(
            product="Product B", review_text="Bad", rating=-1
        )
        assert review1.review_id != review2.review_id

    def test_get_all_empty(self, review_repo):
        """get_all should return empty results when no reviews exist."""
        result = review_repo.get_all()
        assert result["totalItems"] == 0
        assert result["reviews"] == []

    def test_get_all_with_reviews(self, review_repo):
        """get_all should return all stored reviews."""
        review_repo.create(product="P1", review_text="Great!", rating=2)
        review_repo.create(product="P2", review_text="Bad!", rating=-2)

        result = review_repo.get_all()
        assert result["totalItems"] == 2
        assert len(result["reviews"]) == 2

    def test_get_all_pagination(self, review_repo):
        """get_all should support pagination with page and size."""
        for i in range(5):
            review_repo.create(
                product=f"P{i}", review_text=f"Review {i}", rating=i
            )

        # Page 1, size 2
        page1 = review_repo.get_all(page=1, size=2)
        assert page1["totalItems"] == 5
        assert page1["totalPages"] == 3
        assert len(page1["reviews"]) == 2
        assert page1["currentPage"] == 1

        # Page 3, size 2 (last page with 1 item)
        page3 = review_repo.get_all(page=3, size=2)
        assert len(page3["reviews"]) == 1
        assert page3["currentPage"] == 3

    def test_get_all_sort_by_rating_asc(self, review_repo):
        """get_all should sort by rating ascending."""
        review_repo.create(product="A", review_text="Ok", rating=1)
        review_repo.create(product="B", review_text="Best", rating=5)
        review_repo.create(product="C", review_text="Worst", rating=0)

        result = review_repo.get_all(sort_by="rating", sort_order="asc")
        ratings = [r.rating for r in result["reviews"]]
        assert ratings == sorted(ratings)

    def test_get_all_sort_by_rating_desc(self, review_repo):
        """get_all should sort by rating descending."""
        review_repo.create(product="A", review_text="Ok", rating=1)
        review_repo.create(product="B", review_text="Best", rating=5)
        review_repo.create(product="C", review_text="Worst", rating=0)

        result = review_repo.get_all(sort_by="rating", sort_order="desc")
        ratings = [r.rating for r in result["reviews"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_get_all_filter_by_rating(self, review_repo):
        """get_all should filter by rating when rating_filter is provided."""
        review_repo.create(product="A", review_text="Ok", rating=1)
        review_repo.create(product="B", review_text="Great", rating=5)

        result = review_repo.get_all(
            where=[Review.rating == 5]
        )
        assert result["totalItems"] == 1
        assert result["reviews"][0].rating == 5

    def test_get_all_filter_by_product(self, review_repo):
        """get_all should filter by product name."""
        review_repo.create(product="Alpha", review_text="Good", rating=1)
        review_repo.create(product="Beta", review_text="Bad", rating=-1)

        result = review_repo.get_all(
            where=[Review.product.contains("Alpha")]
        )
        assert result["totalItems"] == 1
        assert result["reviews"][0].product == "Alpha"

    def test_get_all_filter_by_review_text(self, review_repo):
        """get_all should filter by review text."""
        review_repo.create(product="A", review_text="This is amazing", rating=5)
        review_repo.create(product="B", review_text="This is terrible", rating=-5)

        result = review_repo.get_all(
            where=[Review.review_text.contains("amazing")]
        )
        assert result["totalItems"] == 1
        assert "amazing" in result["reviews"][0].review_text

    def test_get_by_id_known_issue(self, review_repo):
        """KNOWN ISSUE: get_by_id uses self.model.id but ReviewModel uses review_id.

        This test documents the known bug. When called, get_by_id will look for
        a column named 'id' which doesn't exist on the Review model.
        """
        created = review_repo.create(
            product="Test", review_text="Known issue test", rating=1
        )
        # This should fail because BaseRepository.get_by_id uses self.model.id
        # but ReviewModel has review_id as its primary key.
        with pytest.raises(AttributeError):
            review_repo.get_by_id(created.review_id)
