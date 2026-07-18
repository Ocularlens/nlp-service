from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi import status as http_status
from app.models import Review
from app.infra import init_db
from sqlalchemy.orm import Session, joinedload
from app.repository import ProductRepository
from app.utils import logger, limiter

product_router: APIRouter = APIRouter()


@product_router.get("/{product_name}/reviews/latest")
@limiter.limit("60/minute")
def get_latest_review(
    request: Request,
    product_name: str,
    db: Session = Depends(init_db),
):
    """Get the most recent review for a product (used by leaderboard tooltip)."""
    logger.info(f"{request.state.request_id} - Fetching latest review for product: {product_name}")

    product = ProductRepository(db).get(product_name)
    if not product:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_name}' not found"
        )

    review = (
        db.query(Review)
        .filter(Review.product_id == product.product_id)
        .order_by(Review.created_at.desc())
        .first()
    )

    if not review:
        return {"product_name": product.product_name, "review": None}

    return {
        "product_name": product.product_name,
        "review": {
            "review_id": review.review_id,
            "review_text": review.review_text,
            "rating": review.rating,
            "mood": review.mood,
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
    }


@product_router.get("/{product_name}/reviews")
@limiter.limit("60/minute")
def get_reviews_by_product(
        request: Request,
        product_name: str,
        db: Session = Depends(init_db),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100)
    ):
    logger.info(f"{request.state.request_id} - Fetching reviews for product: {product_name}")

    # Look up product by uppercase name
    product = ProductRepository(db).get(product_name)
    if not product:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_name}' not found"
        )

    # Query reviews for this product with eager-loaded product relationship
    query = (
        db.query(Review)
        .options(joinedload(Review.product))
        .filter(Review.product_id == product.product_id)
    )

    total = query.count()

    if page is not None and size is not None:
        query = query.offset((page - 1) * size).limit(size)

    reviews = query.all()

    return {
        "product_name": product.product_name,
        "totalPages": (total + size - 1) // size,
        "currentPage": page,
        "pageSize": size,
        "totalItems": total,
        "reviews": reviews
    }
