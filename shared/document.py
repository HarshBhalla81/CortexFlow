from pydantic import BaseModel
from typing import Optional
from uuid import uuid4


class Document(BaseModel):
    id: str
    text: str
    source: Optional[str] = None
    metadata: dict = {}