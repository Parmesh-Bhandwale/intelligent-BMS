import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/recommendations")
async def recommend_books():
    logger.info("Generating recommendations")
    return {
        "recommendations": [
            "Clean Architecture",
            "Designing Data-Intensive Applications"
        ]
    }
