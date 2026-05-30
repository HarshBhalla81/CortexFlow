from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    event_type: str
    source: str
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)