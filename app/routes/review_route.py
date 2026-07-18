from fastapi import APIRouter, Depends, Request, Query
from app.services import SpacyInteg, Translator
from app.services.leaderboard import leaderboard_service
from app.models import Review, Product
from app.infra import init_db
from sqlalchemy.orm import Session, contains_eager
from app.repository import ReviewRepository, ProductRepository
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

    # Get or create the product (uppercase lookup)
    product = ProductRepository(db).get_or_create(review.productName)

    new_review = ReviewRepository(db).create(
        product_id=product.product_id,
        review_text=review.text,
        rating=result.get("sentiment_score", 0),
        mood=result.get("mood", "neutral")
    )

    # Update Redis leaderboard (failures should not block review creation)
    try:
        leaderboard_service.update_score(
            review.productName,
            result.get("sentiment_score", 0)
        )
    except Exception as e:
        logger.error(f"{request.state.request_id} - Failed to update leaderboard for {review.productName}: {e}")

    return {
        "message": "Review successfully analyzed and stored",
        "analysis_result": result,
        "review_id": new_review.review_id
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

    # Build query with join to Product and eager-load the relationship
    query = (
        db.query(Review)
        .join(Product, Review.product_id == Product.product_id)
        .options(contains_eager(Review.product))
    )

    # Apply filters
    if rating_filter is not None:
        query = query.filter(Review.rating == rating_filter)
    if product_filter:
        query = query.filter(Product.product_name.contains(product_filter.upper()))
    if review_filter:
        query = query.filter(Review.review_text.contains(review_filter))

    # Apply sorting
    if sort_by:
        if sort_by == "product":
            sort_col = Product.product_name
        else:
            sort_col = getattr(Review, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

    total = query.count()

    if page is not None and size is not None:
        query = query.offset((page - 1) * size).limit(size)

    reviews = query.all()

    return {
        "totalPages": (total + size - 1) // size,
        "currentPage": page,
        "pageSize": size,
        "totalItems": total,
        "reviews": reviews
    }
