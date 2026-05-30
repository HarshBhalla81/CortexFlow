from datetime import datetime
from pydantic import BaseModel, Field


class TaskResult(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)