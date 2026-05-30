import redis
import uuid
from fastapi import APIRouter
from shared.models.task import Task

router = APIRouter()



print("Shared Task Model Imported Successfully")

r = redis.Redis(host="redis", port=6379, decode_responses=True)


@router.post("/request")
async def process_request(data: Task):

    payload = data.model_dump()
    task_id = str(uuid.uuid4())

    r.xadd(
        "agent_stream",
        {
            "task_id": task_id,
            "task_type": payload["task_type"],
            "message": payload["message"]
        }
    )
    r.set(
        f"task:{task_id}:status",
        "queued"
    )
    return {
        "status": "queued",
        "task_id": task_id,
    }