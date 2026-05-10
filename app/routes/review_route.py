from fastapi import APIRouter, Depends, Request
from app.services import SpacyInteg
from app.models import Review
from app.infra import init_db
from sqlalchemy.orm import Session
from app.repository import ReviewRepository
from app.utils import logger, limiter
from app.schema import Review, ReviewResponse 

review_router: APIRouter = APIRouter()
spacy_integ = SpacyInteg()
    
@review_router.post("/")
@limiter.limit("30/minute")
def analyze_review(request: Request, review: Review, db: Session = Depends(init_db)) -> ReviewResponse:
    logger.info(f"{request.state.request_id} - Received review for analysis: {review.text} and product: {review.productName}")
    result = spacy_integ.analyze_string(review.text)

    review = ReviewRepository(db).create(
        product=review.productName,
        review_text=review.text,
        rating=result.get("sentiment_score", 0)
    )
  
    return {
        "message": "Review successfully analyzed and stored",
        "analysis_result": result,
        "review_id": review.review_id
    }

@review_router.get("/")
@limiter.limit("60/minute")
def get_reviews(request: Request, db: Session = Depends(init_db)):
    logger.info(f"{request.state.request_id} - Fetching all reviews")
    reviews = ReviewRepository(db).get_all_reviews()
    logger.info(f"{request.state.request_id} - Retrieved {len(reviews)} reviews")
    return reviews  