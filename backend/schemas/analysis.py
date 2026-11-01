from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class EventOut(BaseModel):
    id: int
    project_id: str
    event_type: str
    stage: str
    message: str
    file_name: str | None = None
    percentage: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageIn(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    id: int
    project_id: str
    role: str
    message_type: str
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ControlAction(BaseModel):
    action: Literal["pause", "resume"]
