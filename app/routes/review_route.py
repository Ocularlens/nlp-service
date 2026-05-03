from fastapi import APIRouter, Depends, Request
from app.services import SpacyInteg
from pydantic import BaseModel
from app.models import Review
from app.infra import init_db
from sqlalchemy.orm import Session
from app.utils import logger

review_router: APIRouter = APIRouter()
spacy_integ = SpacyInteg()

class Review(BaseModel):
    text: str

@review_router.post("/")
def analyze_review(request: Request,review: Review, db: Session = Depends(init_db)):
    print(request.state.request_id)  # log the request ID for tracing
    result = spacy_integ.analyze_string(review.text)

    # reviews = db.get(Review, 1).all()

    # logger.info(reviews)

    return {"result": result}