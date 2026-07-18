"""Leaderboard API routes."""
from fastapi import APIRouter, Request, Query
from app.utils import logger, limiter
from app.services.leaderboard import leaderboard_service

leaderboard_router = APIRouter()


@leaderboard_router.get("/")
@limiter.limit("30/minute")
def get_leaderboard(
    request: Request,
    limit: int = Query(10, ge=1, le=100)
):
    """Get the top products ranked by total sentiment score.

    Queries Redis (in-memory leaderboard) instead of the database.
    """
    logger.info(f"{request.state.request_id} - Fetching leaderboard, limit={limit}")

    top_products = leaderboard_service.get_top_products(limit)

    return {
        "leaderboard": top_products,
        "limit": limit,
        "total": len(top_products)
    }
