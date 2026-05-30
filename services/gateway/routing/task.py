import redis
from fastapi import APIRouter
from shared.models.task import Task
import json
router = APIRouter()



print("Shared Task Model Imported Successfully")

r = redis.Redis(host="redis", port=6379, decode_responses=True)


@router.post("/request")
async def process_request(data: Task):

    task = data

    payload = task.model_dump()
    task_id = payload["task_id"]
    r.xadd(
        "agent_stream",
        {
            "task_id": task_id,
            "task_type": payload["task_type"],
            "payload": json.dumps(payload["payload"])
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