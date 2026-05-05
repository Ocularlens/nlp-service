from fastapi import APIRouter, Depends, Request
from app.services import SpacyInteg
from pydantic import BaseModel
from app.models import Review
from app.infra import init_db
from sqlalchemy.orm import Session
from app.repository import ReviewRepository
from app.utils import logger

review_router: APIRouter = APIRouter()
spacy_integ = SpacyInteg()

class Review(BaseModel):
    text: str
    productName: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This product is amazing! It exceeded my expectations.",
                "productName": "SuperWidget 3000"
            }
        }
        
class ReviewResponse(BaseModel):
    message: str
    analysis_result: dict
    review_id: int
    
@review_router.post("/")
def analyze_review(request: Request,review: Review, db: Session = Depends(init_db)) -> ReviewResponse:
    logger.info(f"{request.state.request_id} - Received review for analysis: {review.text} and product: {review.productName}")
    result = spacy_integ.analyze_string(review.text)

    review = ReviewRepository(db).create_review(
        product=review.productName,
        review_text=review.text,
        rating=result.get("sentiment_score", 0)
    )
    logger.info(f"{request.state.request_id} - Review analyzed and stored: {review.review_id}")
     
    return {
        "message": "Review successfully analyzed and stored",
        "analysis_result": result,
        "review_id": review.review_id
    }