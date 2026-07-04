"""
Test configuration and fixtures for nlp-service.

Sets up:
- Environment variables before app imports (memory:// Redis, SQLite DB)
- Temporary file-based SQLite database (avoids per-connection isolation of :memory:)
- Mocked Translator to avoid real Google Translate API calls
- FastAPI TestClient with overridden dependencies
"""
import os
import tempfile
import pytest
from typing import Generator
from unittest.mock import patch

# Set test environment BEFORE importing any app modules
# This ensures the rate limiter uses in-memory storage (no Redis needed)
# and the database uses SQLite (no PostgreSQL needed)
os.environ["REDIS_URL"] = "memory://"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.main import server
from app.infra.database import Base, init_db


@pytest.fixture(autouse=True)
def mock_translator():
    """Mock GoogleTranslator to prevent real HTTP calls during tests.

    This patches the GoogleTranslator class used in both:
    - app.services.translator (route-level translation)
    - app.schema.review_schema (language code validation)
    """
    with patch("deep_translator.GoogleTranslator") as mock_gt:
        instance = mock_gt.return_value
        instance.translate.return_value = "translated test text"
        # Provide some supported languages for schema validation
        instance.get_supported_languages.return_value = ["en", "es", "fr", "de"]
        yield


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient with SQLite database dependency override.

    Uses a temporary file-based SQLite database to avoid per-connection
    isolation issues that occur with :memory: databases when TestClient
    runs requests in a separate thread.

    Creates all tables before each test and cleans up the database file after.
    """
    # Create a temporary file for the SQLite database
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)

    # Create engine with NullPool and check_same_thread=False
    # to support cross-thread access from TestClient
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    Base.metadata.create_all(engine)

    TestSession = sessionmaker(bind=engine)

    def override_init_db() -> Generator[Session, None, None]:
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    server.dependency_overrides[init_db] = override_init_db
    yield TestClient(server)

    # Cleanup
    server.dependency_overrides.clear()
    engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def db_session(test_client: TestClient) -> Generator[Session, None, None]:
    """Provide a SQLAlchemy session for direct database testing.

    This fixture depends on test_client so that the dependency override
    is already registered. It creates a fresh session bound to the same
    SQLite database file used by test_client.
    """
    # We need a session that connects to the same database used by the
    # test_client override. Since test_client manages the engine, we
    # just yield a basic session.
    from app.infra.database import database as app_database
    engine = create_engine(
        str(app_database.url),
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_review() -> dict:
    """Provide a sample valid review request payload."""
    return {
        "text": "This product is amazing! It exceeded my expectations.",
        "productName": "SuperWidget 3000",
    }


@pytest.fixture
def sample_translation() -> dict:
    """Provide a sample translation payload."""
    return {
        "source_language": "es",
    }


@pytest.fixture
def sample_review_with_translation(sample_review, sample_translation) -> dict:
    """Provide a sample review with translation."""
    return {
        **sample_review,
        "translation": sample_translation,
    }
