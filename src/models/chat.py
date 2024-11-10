from pydantic import BaseModel

from models.user import User


class ChatBase(BaseModel):
    user1: User
    user2: User


class Chat(ChatBase):
    id: str
