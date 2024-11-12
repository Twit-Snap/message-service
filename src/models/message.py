from typing import Optional
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    content: str
    receiver_expo_token: Optional[str] = Field(default=None, exclude=True)


class Message(MessageBase):
    id: str
    sender_id: int
    created_at: str
