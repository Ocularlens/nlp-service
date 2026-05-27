from fastapi import APIRouter, Depends, Request, Query
from app.services import SpacyInteg, Translator
from app.models import Review
from app.infra import init_db
from sqlalchemy.orm import Session
from app.repository import ReviewRepository
from app.utils import logger, limiter
from app.schema import ReviewRequest, ReviewResponse 

review_router: APIRouter = APIRouter()
spacy_integ = SpacyInteg()

@review_router.post("/")
@limiter.limit("30/minute")
def analyze_review(request: Request, review: ReviewRequest, db: Session = Depends(init_db)) -> ReviewResponse:
    logger.info(f"{request.state.request_id} - Received review for analysis: {review.text} and product: {review.productName}")
    
    if review.translation:
        review.text = Translator.translate(review.text, review.translation.source_language)
        logger.info(f"{request.state.request_id} - Translation completed: {review.text}")
    
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
def get_reviews(
        request: Request, 
        db: Session = Depends(init_db),
        sort_by: str = Query("review_id", enum=["review_id", "rating", "product"]),
        sort_order: str = Query("desc", enum=["asc", "desc"]),
        rating_filter: int = Query(None, ge=1, le=5),
        product_filter: str = Query(None),
        review_filter: str = Query(None),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100)
    ):
    logger.info(f"{request.state.request_id} - Fetching all reviews")
    reviews = ReviewRepository(db).get_all(
        sort_by=sort_by,
        sort_order=sort_order,
        where=[
            Review.rating == rating_filter if rating_filter is not None else True,
            Review.product.contains(product_filter) if product_filter else True,
            Review.review_text.contains(review_filter) if review_filter else True
        ],
        page=page,
        size=size
    )
    logger.info(f"{request.state.request_id} - Retrieved {len(reviews)} reviews")
    return reviews