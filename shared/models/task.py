from pydantic import BaseModel

class Task(BaseModel):
    task_id: str
    task_type: str
    message: str