import redis
import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

@router.get("/health")
async def health_check():

    try:
        logger.info("Health check requested")
        r.ping()

        return {
            "status": "healthy",
            "redis": True
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "redis": False,
            "error": str(e)
        }