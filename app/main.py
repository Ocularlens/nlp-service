from fastapi import FastAPI, Request
from app.routes import review_router
from app.utils import logger
import uuid

server = FastAPI()

@server.get("/health")
def root():
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