# Copilot Instructions for NLP Service

## Project Overview
This is a **FastAPI microservice** for analyzing product reviews using NLP (sentiment analysis via spaCy). It provides REST API endpoints for submitting reviews, storing them in PostgreSQL, and retrieving aggregated results with filtering/sorting capabilities.

## Build, Test, and Lint

### Running the Service
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download required spaCy model (run once)
python -m spacy download en_core_web_sm

# Run development server with auto-reload
uvicorn app.main:server --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:server --host 0.0.0.0 --port 8000
```

### Database Migrations (Alembic)
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of change"

# Apply pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current database state
alembic current
```

### Environment Setup
Create/update `.env` file with:
```
DATABASE_URL=postgresql://user:password@localhost:5432/product_reviews
REDIS_URL=redis://:password@localhost:6379
```

The database and Redis services must be running for the application to start properly.

## High-Level Architecture

### Component Layers
1. **Routes** (`app/routes/`) - FastAPI routers that define HTTP endpoints
   - Request/response handling
   - Route protection via rate limiting
   - Request tracing via middleware-injected request IDs

2. **Services** (`app/services/`) - Business logic layer
   - `SpacyInteg`: NLP sentiment analysis (positive/negative word detection with negation handling)
   - `Translator`: Multi-language translation support using `deep-translator`

3. **Repository** (`app/repository/`) - Data access layer
   - `BaseRepository`: Generic CRUD operations with sorting, filtering, pagination
   - `ReviewRepository`: Review-specific queries
   - Handles all database transactions via SQLAlchemy Session

4. **Models** (`app/models/`) - SQLAlchemy ORM definitions
   - `ReviewModel`: Maps to `reviews` table with fields: review_id (PK), product, review_text, rating

5. **Schema** (`app/schema/`) - Pydantic models for validation
   - Input validation (ReviewRequest)
   - Structured response types (ReviewResponse)

6. **Infrastructure** (`app/infra/`)
   - Database engine initialization and session management
   - SQLAlchemy Base class for ORM models

7. **Utils** (`app/utils/`)
   - `logger`: Uvicorn logger instance for structured logging
   - `limiter`: Slowapi rate limiter configured for endpoints
   - `unique_id`: Utility for generating unique identifiers

### Data Flow for Review Analysis
1. Request arrives at `POST /api/v1/reviews/` endpoint
2. Middleware adds unique `request_id` for tracing
3. Pydantic schema validates and parses request
4. Optional translation via `Translator` service
5. `SpacyInteg.analyze_string()` performs sentiment analysis
6. `ReviewRepository` persists review and sentiment score to PostgreSQL
7. Structured response returned with analysis results

## Key Conventions

### Repository Pattern
All database access goes through repository classes extending `BaseRepository`:
```python
# Repository method signatures
.create(**kwargs)          # Insert and return new instance
.get_by_id(id)             # Fetch by primary key
.get_all(sort_by, sort_order, where, page, size)  # Query with pagination
.update(id, **kwargs)      # Modify and persist
.delete(id)                # Remove record
```

- `sort_by`: Field name to sort on (matches model attribute names)
- `sort_order`: "asc" or "desc"
- `where`: SQLAlchemy filter conditions (single or list of conditions)
- `page`/`size`: Pagination parameters (1-indexed pages)
- Returns dict with pagination metadata and results under `model.__tablename__` key

### Dependency Injection
FastAPI's `Depends()` is used for injecting services:
```python
def endpoint(request: Request, db: Session = Depends(init_db)):
    # db is automatically provided SQLAlchemy session
    # request.state.request_id is available for logging
```

Every endpoint that accesses the database must depend on `init_db` to get a valid database session.

### Logging Convention
All logging uses the centralized `logger` from `app.utils.logger`:
```python
from app.utils import logger

logger.info(f"{request.state.request_id} - Message describing action")
logger.error(f"{request.state.request_id} - Error context")
```

Include `request_id` in log messages for request tracing across logs.

### Rate Limiting
Decorators specify rate limits per endpoint:
```python
@limiter.limit("30/minute")  # 30 requests per minute
def endpoint(request: Request):
    pass
```

Common limits in codebase: 30/minute for write operations, 60/minute for reads.

### Error Handling
The main application includes generic exception handler that:
- Logs unhandled exceptions with `request_id`
- Returns JSON error response with status 500
- Never exposes internal traceback details to clients

### Testing Access Patterns
- Endpoints are stateless and depend on database session
- Request tracing enabled via middleware-injected `request.state.request_id`
- Health check endpoint (`GET /health`) available for service status verification

### NLP Sentiment Analysis Details
`SpacyInteg.analyze_string()` returns:
- `mood`: "positive", "negative", "neutral", or "mixed"
- `sentiment_score`: Difference between positive and negative word counts
- `positive_count`/`negative_count`: Individual word counts
- `signals`: List of detected words with context (e.g., "negated positive: 'not good'")

Negation handling: Words preceded by negation tokens (not, never, no, n't, neither, nor) flip sentiment polarity.

### Translation Service
`Translator.translate(text, source_language)` converts review text to English before NLP analysis. Source language specified in optional `translation` field of review request.

## Docker
```bash
# Build image
docker build -t nlp-service:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/db \
  -e REDIS_URL=redis://:password@host:6379 \
  nlp-service:latest
```

Dockerfile uses Python 3.11-slim and pre-downloads spaCy model during build.
