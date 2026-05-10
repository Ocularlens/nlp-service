from app.infra import Base
from sqlalchemy import Column, Integer, String

class ReviewModel(Base):
    __tablename__ = "reviews"

    review_id = Column(String(64), nullable=False, unique=True, index=True, primary_key=True)
    product = Column(String(64), nullable=False, index=True)
    review_text = Column(String(120), nullable=False)
    rating = Column(Integer, nullable=False)