"""Tests for the ReviewRepository class."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infra.database import Base
from app.repository import ReviewRepository
from app.models import Review, Product


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


def _create_product(session, product_id: str, product_name: str) -> Product:
    """Helper to create a Product in the test database."""
    product = Product(product_id=product_id, product_name=product_name)
    session.add(product)
    session.commit()
    return product


class TestReviewRepository:
    """Test suite for ReviewRepository CRUD operations."""

    def test_create_review(self, review_repo, repo_session):
        """Creating a review should persist it and return it with a review_id."""
        _create_product(repo_session, "prod-1", "TEST PRODUCT")
        review = review_repo.create(
            product_id="prod-1",
            review_text="This is a great product!",
            rating=2,
            mood="positive",
        )
        assert review.review_id is not None
        assert len(review.review_id) == 36  # UUID length
        assert review.product_id == "prod-1"
        assert review.review_text == "This is a great product!"
        assert review.rating == 2
        assert review.mood == "positive"

    def test_create_generates_unique_ids(self, review_repo, repo_session):
        """Each created review should get a unique review_id."""
        _create_product(repo_session, "prod-a", "PRODUCT A")
        _create_product(repo_session, "prod-b", "PRODUCT B")
        review1 = review_repo.create(
            product_id="prod-a", review_text="Good", rating=1, mood="positive"
        )
        review2 = review_repo.create(
            product_id="prod-b", review_text="Bad", rating=-1, mood="negative"
        )
        assert review1.review_id != review2.review_id

    def test_get_all_empty(self, review_repo):
        """get_all should return empty results when no reviews exist."""
        result = review_repo.get_all()
        assert result["totalItems"] == 0
        assert result["reviews"] == []

    def test_get_all_with_reviews(self, review_repo, repo_session):
        """get_all should return all stored reviews."""
        _create_product(repo_session, "p1", "P1")
        _create_product(repo_session, "p2", "P2")
        review_repo.create(product_id="p1", review_text="Great!", rating=2, mood="positive")
        review_repo.create(product_id="p2", review_text="Bad!", rating=-2, mood="negative")

        result = review_repo.get_all()
        assert result["totalItems"] == 2
        assert len(result["reviews"]) == 2

    def test_get_all_pagination(self, review_repo, repo_session):
        """get_all should support pagination with page and size."""
        for i in range(5):
            _create_product(repo_session, f"p{i}", f"P{i}")
            review_repo.create(
                product_id=f"p{i}", review_text=f"Review {i}", rating=i, mood="neutral"
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

    def test_get_all_sort_by_rating_asc(self, review_repo, repo_session):
        """get_all should sort by rating ascending."""
        _create_product(repo_session, "a", "A")
        _create_product(repo_session, "b", "B")
        _create_product(repo_session, "c", "C")
        review_repo.create(product_id="a", review_text="Ok", rating=1, mood="neutral")
        review_repo.create(product_id="b", review_text="Best", rating=5, mood="positive")
        review_repo.create(product_id="c", review_text="Worst", rating=0, mood="neutral")

        result = review_repo.get_all(sort_by="rating", sort_order="asc")
        ratings = [r.rating for r in result["reviews"]]
        assert ratings == sorted(ratings)

    def test_get_all_sort_by_rating_desc(self, review_repo, repo_session):
        """get_all should sort by rating descending."""
        _create_product(repo_session, "a", "A")
        _create_product(repo_session, "b", "B")
        _create_product(repo_session, "c", "C")
        review_repo.create(product_id="a", review_text="Ok", rating=1, mood="neutral")
        review_repo.create(product_id="b", review_text="Best", rating=5, mood="positive")
        review_repo.create(product_id="c", review_text="Worst", rating=0, mood="neutral")

        result = review_repo.get_all(sort_by="rating", sort_order="desc")
        ratings = [r.rating for r in result["reviews"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_get_all_filter_by_rating(self, review_repo, repo_session):
        """get_all should filter by rating when rating_filter is provided."""
        _create_product(repo_session, "a", "A")
        _create_product(repo_session, "b", "B")
        review_repo.create(product_id="a", review_text="Ok", rating=1, mood="neutral")
        review_repo.create(product_id="b", review_text="Great", rating=5, mood="positive")

        result = review_repo.get_all(
            where=[Review.rating == 5]
        )
        assert result["totalItems"] == 1
        assert result["reviews"][0].rating == 5

    def test_get_all_filter_by_product(self, review_repo, repo_session):
        """get_all should filter by product name."""
        _create_product(repo_session, "id-alpha", "Alpha")
        _create_product(repo_session, "id-beta", "Beta")
        review_repo.create(product_id="id-alpha", review_text="Good", rating=1, mood="positive")
        review_repo.create(product_id="id-beta", review_text="Bad", rating=-1, mood="negative")

        result = review_repo.get_all(
            where=[Review.product.has(Product.product_name.contains("Alpha"))]
        )
        assert result["totalItems"] == 1
        assert result["reviews"][0].product.product_name == "Alpha"

    def test_get_all_filter_by_review_text(self, review_repo, repo_session):
        """get_all should filter by review text."""
        _create_product(repo_session, "a", "A")
        _create_product(repo_session, "b", "B")
        review_repo.create(product_id="a", review_text="This is amazing", rating=5, mood="positive")
        review_repo.create(product_id="b", review_text="This is terrible", rating=-5, mood="negative")

        result = review_repo.get_all(
            where=[Review.review_text.contains("amazing")]
        )
        assert result["totalItems"] == 1
        assert "amazing" in result["reviews"][0].review_text

    def test_get_by_id_known_issue(self, review_repo, repo_session):
        """KNOWN ISSUE: get_by_id uses self.model.id but ReviewModel uses review_id.

        This test documents the known bug. When called, get_by_id will look for
        a column named 'id' which doesn't exist on the Review model.
        """
        _create_product(repo_session, "id-test", "Test")
        created = review_repo.create(
            product_id="id-test", review_text="Known issue test", rating=1, mood="neutral"
        )
        # This should fail because BaseRepository.get_by_id uses self.model.id
        # but ReviewModel has review_id as its primary key.
        with pytest.raises(AttributeError):
            review_repo.get_by_id(created.review_id)
