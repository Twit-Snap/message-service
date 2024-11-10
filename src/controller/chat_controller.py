from models.chat import ChatBase
from models.errors.errors import ValidationError


class ChatController:
    def validate_users(self, chat: ChatBase):
        if not chat.user1.id or not chat.user2.id or not chat.user1.username or not chat.user2.username:
            raise ValidationError(
                title="No user provided",
                detail="You must provide two users to create a chat"
            )
