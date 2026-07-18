from app.infra import Base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import relationship


class ReviewModel(Base):
    __tablename__ = "reviews"

    review_id = Column(String(64), nullable=False, unique=True, index=True, primary_key=True)
    product_id = Column(String(64), ForeignKey("products.product_id"), nullable=False, index=True)
    review_text = Column(String(120), nullable=False)
    rating = Column(Integer, nullable=False)
    mood = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    product = relationship("ProductModel", back_populates="reviews")
