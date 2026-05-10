from app.models import Review
from app.utils import generate_unique_id
from .base_repository import BaseRepository

class ReviewRepository(BaseRepository):
    def __init__(self, db_session):
        super().__init__(db_session, Review)

    def create(self, **review_data):
        review_id = generate_unique_id()
        review_data['review_id'] = review_id
        new_review = super().create(**review_data)
       
        return new_review