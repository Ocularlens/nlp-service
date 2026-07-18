from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.routes import review_router, leaderboard_router
from app.utils import logger, limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os

server = FastAPI(
    title="Review Service",
    description="A microservice for handling product reviews",
    version="1.0.0"
)

server.state.limiter = limiter
server.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

server.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Path to the static frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")


@server.get("/")
def serve_frontend():
    """Serve the single-page frontend application."""
    return FileResponse(INDEX_HTML)


@server.get("/health")
@limiter.limit("60/minute")
def root(request: Request):
    '''Health check endpoint
    Returns:
        dict: A message indicating the service is healthy
    '''
    logger.info("Health check endpoint called")
    return {"message": "Service is healthy!"}


@server.middleware("http")
async def add_request_id(request: Request, call_next):
  request_id = str(uuid.uuid4())
  request.state.request_id = request_id  # accessible in routes
  response = await call_next(request)
  response.headers["X-Request-ID"] = request_id  # added to response headers
  
  return response

server.include_router(review_router, prefix="/api/v1/reviews", tags=["reviews"])
server.include_router(leaderboard_router, prefix="/api/v1/leaderboard", tags=["leaderboard"])

@server.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred. Please try again later."}
    )

# Mount static files AFTER all routes so it doesn't shadow them
server.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
