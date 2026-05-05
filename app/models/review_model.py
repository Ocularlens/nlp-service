from app.infra import Base
from sqlalchemy import Column, Integer, String

class ReviewModel(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(64), nullable=False, unique=True, index=True)
    product = Column(String(64), nullable=False, index=True)
    review_text = Column(String(120), nullable=False)
    rating = Column(Integer, nullable=False)