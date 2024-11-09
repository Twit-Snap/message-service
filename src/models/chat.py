from pydantic import BaseModel


class ChatBase(BaseModel):
    user1_id: int
    user2_id: int


class Chat(ChatBase):
    id: str
