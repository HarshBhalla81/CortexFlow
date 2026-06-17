import logging
from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/result/{task_id}")
async def get_result(task_id: str):
    # With the new passthrough architecture, results are written directly to 
    # CSV by Pathway. This endpoint is currently stubbed until a dedicated 
    # results service or Pathway endpoint is implemented.
    logger.info(f"Result requested for task {task_id}, but Redis has been removed.")
    
    return {
        "status": "pending",
        "message": "Results querying is currently disabled in the passthrough architecture."
    }
