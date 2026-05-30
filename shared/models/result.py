from pydantic import BaseModel

class TaskResult(BaseModel):
    task_id: str
    status: str
    result: str