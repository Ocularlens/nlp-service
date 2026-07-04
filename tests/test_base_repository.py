"""Tests for the BaseRepository class."""

import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from app.infra.database import Base
from app.repository import BaseRepository


# A simple test model for BaseRepository tests.
# Prefix with underscore to prevent pytest collection warnings.
class _TestModel(Base):
    """A lightweight model for testing BaseRepository independently."""

    __tablename__ = "test_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    value = Column(Integer, default=0)


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
def base_repo(repo_session):
    """Create a BaseRepository bound to the test session and _TestModel."""
    return BaseRepository(repo_session, _TestModel)


class TestBaseRepository:
    """Test suite for BaseRepository CRUD operations."""

    def test_create(self, base_repo):
        """Creating an instance should persist it and return it with an id."""
        instance = base_repo.create(name="Test", value=42)
        assert instance.id is not None
        assert instance.name == "Test"
        assert instance.value == 42

    def test_get_by_id(self, base_repo):
        """get_by_id should retrieve an instance by its primary key 'id'."""
        created = base_repo.create(name="Find Me", value=1)
        found = base_repo.get_by_id(created.id)
        assert found is not None
        assert found.name == "Find Me"
        assert found.id == created.id

    def test_get_by_id_not_found(self, base_repo):
        """get_by_id should return None when id does not exist."""
        found = base_repo.get_by_id(999)
        assert found is None

    def test_get_all_empty(self, base_repo):
        """get_all should return empty results when no records exist."""
        result = base_repo.get_all()
        assert result["totalItems"] == 0
        assert result["test_model"] == []

    def test_get_all_with_records(self, base_repo):
        """get_all should return all records."""
        base_repo.create(name="A", value=1)
        base_repo.create(name="B", value=2)

        result = base_repo.get_all()
        assert result["totalItems"] == 2
        assert len(result["test_model"]) == 2

    def test_get_all_sort_by_value_asc(self, base_repo):
        """get_all should sort by value ascending."""
        base_repo.create(name="C", value=3)
        base_repo.create(name="A", value=1)
        base_repo.create(name="B", value=2)

        result = base_repo.get_all(sort_by="value", sort_order="asc")
        values = [r.value for r in result["test_model"]]
        assert values == [1, 2, 3]

    def test_get_all_sort_by_value_desc(self, base_repo):
        """get_all should sort by value descending."""
        base_repo.create(name="A", value=1)
        base_repo.create(name="B", value=2)
        base_repo.create(name="C", value=3)

        result = base_repo.get_all(sort_by="value", sort_order="desc")
        values = [r.value for r in result["test_model"]]
        assert values == [3, 2, 1]

    def test_get_all_pagination(self, base_repo):
        """get_all should return paginated results."""
        for i in range(1, 11):
            base_repo.create(name=f"Item {i}", value=i)

        page1 = base_repo.get_all(page=1, size=3)
        assert len(page1["test_model"]) == 3
        assert page1["totalItems"] == 10
        assert page1["totalPages"] == 4
        assert page1["currentPage"] == 1

        page4 = base_repo.get_all(page=4, size=3)
        assert len(page4["test_model"]) == 1  # last page has 1 item

    def test_get_all_with_where_filter(self, base_repo):
        """get_all with a where clause should filter results."""
        base_repo.create(name="Apple", value=5)
        base_repo.create(name="Banana", value=10)
        base_repo.create(name="Cherry", value=5)

        result = base_repo.get_all(where=[_TestModel.value == 5])
        assert result["totalItems"] == 2

    def test_get_all_with_multiple_where_filters(self, base_repo):
        """get_all with multiple where clauses should apply all."""
        base_repo.create(name="Apple", value=5)
        base_repo.create(name="Banana", value=10)
        base_repo.create(name="Apple", value=10)

        result = base_repo.get_all(
            where=[_TestModel.name == "Apple", _TestModel.value == 10]
        )
        assert result["totalItems"] == 1

    def test_update(self, base_repo):
        """Update should modify fields and return the updated instance."""
        created = base_repo.create(name="Original", value=1)
        updated = base_repo.update(created.id, name="Updated", value=99)
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.value == 99

        # Verify persistence
        fetched = base_repo.get_by_id(created.id)
        assert fetched.name == "Updated"

    def test_update_not_found(self, base_repo):
        """Update should return None when id does not exist."""
        result = base_repo.update(999, name="Ghost")
        assert result is None

    def test_delete(self, base_repo):
        """Delete should remove the instance and return True."""
        created = base_repo.create(name="Delete Me", value=0)
        assert base_repo.delete(created.id) is True
        assert base_repo.get_by_id(created.id) is None

    def test_delete_not_found(self, base_repo):
        """Delete should return False when id does not exist."""
        assert base_repo.delete(999) is False

    def test_delete_twice(self, base_repo):
        """Deleting the same instance twice should return False the second time."""
        created = base_repo.create(name="Double Delete", value=0)
        assert base_repo.delete(created.id) is True
        assert base_repo.delete(created.id) is False
