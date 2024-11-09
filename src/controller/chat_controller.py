from models.chat import ChatBase
from models.errors.errors import ValidationError


class ChatController:
    def validate_users(self, chat: ChatBase):
        if not chat.user1_id or not chat.user2_id:
            raise ValidationError(
                title="No user provided",
                detail="You must provide two users to create a chat"
            )
