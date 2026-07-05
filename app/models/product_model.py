from app.infra import Base
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class ProductModel(Base):
    __tablename__ = "products"

    product_id = Column(String(64), nullable=False, unique=True, index=True, primary_key=True)
    product_name = Column(String(64), nullable=False, unique=True, index=True)

    reviews = relationship("ReviewModel", back_populates="product")
