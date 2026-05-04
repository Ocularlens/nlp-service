from app.models import Review
from app.utils import generate_unique_id

class ReviewRepository:
    def __init__(self, db_session):
        self.db_session = db_session

    def create_review(self, product: str, review_text: str, rating: int) -> Review:
        new_review = Review(
            review_id=generate_unique_id(),
            product=product,
            review_text=review_text,
            rating=rating
        )
        self.db_session.add(new_review)
        self.db_session.commit()
        self.db_session.refresh(new_review)
        return new_review

    def get_review_by_id(self, review_id: str) -> Review:
        return self.db_session.query(Review).filter(Review.review_id == review_id).first()