import redis
from fastapi import APIRouter

router = APIRouter()

r = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

@router.get("/result/{task_id}")
async def get_result(task_id: str):

    status = r.get(
        f"task:{task_id}:status"
    )

    if not status:
        return {
            "error": "Task not found"
        }

    if status == "completed":

        result = r.get(
            f"result:{task_id}"
        )

        return {
            "status": status,
            "result": result
        }

    return {
        "status": status
    }
