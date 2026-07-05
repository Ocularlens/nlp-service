from typing import Optional

from app.models import Product
from app.utils import generate_unique_id
from .base_repository import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self, db_session):
        super().__init__(db_session, Product)

    def get(self, product_name: str) -> Optional[Product]:
        """Lookup product by uppercase name; return None if not found."""
        upper_name = product_name.upper()
        return self.db.query(Product).filter(Product.product_name == upper_name).first()

    def get_or_create(self, product_name: str) -> Product:
        """Lookup product by uppercase name; create if not found."""
        existing = self.get(product_name)
        if existing:
            return existing
        return self.create(
            product_id=generate_unique_id(),
            product_name=product_name.upper()
        )
