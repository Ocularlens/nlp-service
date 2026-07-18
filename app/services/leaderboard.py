"""
Leaderboard service using Redis Sorted Sets to rank products by review sentiment.
"""
import os
import logging

import redis

LEADERBOARD_KEY = "product_leaderboard"

logger = logging.getLogger("uvicorn.access")


class LeaderboardService:
    """Manages a Redis Sorted Set leaderboard of products ranked by sentiment score.

    Uses ZINCRBY to increment scores when new reviews arrive and ZREVRANGE
    to retrieve the top-ranked products.
    """

    def __init__(self, redis_client=None):
        """Initialize with an optional Redis client (for test injection).
        If no client is provided, creates one from REDIS_URL env var.
        """
        self.redis = redis_client
        self.key = LEADERBOARD_KEY
        if self.redis is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            try:
                self.redis = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(
                    f"Leaderboard unavailable: could not connect to Redis "
                    f"at {redis_url}: {e}"
                )
                self.redis = None

    def _available(self) -> bool:
        """Check if the Redis client is available."""
        return self.redis is not None

    def update_score(self, product_name: str, sentiment_score: int) -> None:
        """Add the sentiment score to the product's total using ZINCRBY.

        Args:
            product_name: The product name (will be uppercased).
            sentiment_score: The sentiment score from analysis (can be negative).
        """
        if not self._available():
            return
        try:
            self.redis.zincrby(self.key, sentiment_score, product_name.upper())
        except redis.RedisError as e:
            logger.error(f"Redis error updating leaderboard for {product_name}: {e}")

    def get_top_products(self, limit: int = 10) -> list:
        """Return the top N products by total sentiment score (descending).

        Args:
            limit: Number of products to return (default 10).

        Returns:
            List of dicts with 'product_name' and 'total_score' keys.
        """
        if not self._available():
            return []
        try:
            results = self.redis.zrevrange(self.key, 0, limit - 1, withscores=True)
            return [
                {"product_name": name.decode() if isinstance(name, bytes) else name,
                 "total_score": int(score)}
                for name, score in results
            ]
        except redis.RedisError as e:
            logger.error(f"Redis error fetching leaderboard: {e}")
            return []

    def get_all_products(self) -> list:
        """Return all products with their scores, sorted by score descending."""
        if not self._available():
            return []
        try:
            results = self.redis.zrevrange(self.key, 0, -1, withscores=True)
            return [
                {"product_name": name.decode() if isinstance(name, bytes) else name,
                 "total_score": int(score)}
                for name, score in results
            ]
        except redis.RedisError as e:
            logger.error(f"Redis error fetching all products: {e}")
            return []

    def clear(self) -> None:
        """Clear the leaderboard (useful for testing)."""
        if not self._available():
            return
        try:
            self.redis.delete(self.key)
        except redis.RedisError as e:
            logger.error(f"Redis error clearing leaderboard: {e}")


# Module-level singleton for production use
leaderboard_service = LeaderboardService()
