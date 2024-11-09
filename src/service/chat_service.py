from models.chat import Chat, ChatBase
from models.errors.errors import MessageMaxLengthException
from models.message import Message, MessageBase
from repository.firebase_db import FirebaseDB


class ChatService:
    def __init__(self, repository: FirebaseDB | None = None):
        self.repository: FirebaseDB = repository or FirebaseDB()

    def validate_message(self, message: str):
        if len(message) > 280:
            raise MessageMaxLengthException()

    def create_chat(self, chat: ChatBase) -> Chat:
        chat_key: str = self.repository.create_chat(
            chat.user1_id, chat.user2_id
        )

        return Chat(
            **(dict(chat)),
            id=chat_key
        )

    def send_message(self, message: MessageBase, user_id: int, chat_id: str) -> Message:
        self.validate_message(message.content)

        created_message = self.repository.send_message(
            chat_id, user_id, message.content
        )

        return Message(**(dict(created_message)))

    def edit_message(self, message: MessageBase, user_id: int, chat_id: str, message_id: str) -> Message:
        self.validate_message(message.content)

        updated_message = self.repository.edit_message(
            chat_id, message_id, message.content, user_id
        )

        return Message(**(dict(updated_message)))

    def delete_message(self, user_id: int, chat_id: str, message_id: str) -> None:
        self.repository.delete_message(
            chat_id, message_id, user_id
        )
