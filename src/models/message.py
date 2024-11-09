from pydantic import BaseModel


class MessageBase(BaseModel):
    content: str


class Message(MessageBase):
    id: str
    sender_id: int
    timestamp: str
