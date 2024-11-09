import datetime
from typing import Any
from os import environ
from json import dumps
from firebase_admin import db


class FirebaseDB:
    def __init__(self):
        """Initialize Firebase connection"""
        self.root = db.reference('/')

    def send_message(self, chat_id: str, user_id: int, message: str) -> dict:
        """Send a message in a chat"""
        messages_ref = self.root.child('messages').child(chat_id)
        message_data = {
            'content': message,
            'sender_id': user_id,
            'timestamp': datetime.datetime.now().isoformat()
        }

        new_message = messages_ref.push(message_data)  # type: ignore

        chat_ref = self.root.child("chats").child(chat_id)

        chat_value = chat_ref.get()

        chat_value.update(  # type: ignore
            {"updated_at": datetime.datetime.now().isoformat()})  # type: ignore

        chat_ref.set(chat_value)

        return {
            'id': new_message.key,
            **message_data
        }

    def __chat_exist(self, user1_id: int, user2_id: int) -> str:
        chats: dict[str, Any] = self.get_user_chats(user1_id)

        participants: dict[str, int] = {
            "user1_id": min(user1_id, user2_id),
            "user2_id": max(user1_id, user2_id)
        }

        for key, chat in chats.items():
            if chat["participants"] == participants:
                return key

        return ''

    def create_chat(self, user1_id: int, user2_id: int) -> str:
        """Create a new chat between two users"""
        existent_chat_key = self.__chat_exist(user1_id, user2_id)

        if len(existent_chat_key) > 0:
            return existent_chat_key

        chat_ref = self.root.child('chats')
        chat_data = {
            'participants': {
                "user1_id": min(user1_id, user2_id),
                "user2_id": max(user1_id, user2_id)
            },
            'created_at': datetime.datetime.now().isoformat()
        }
        new_chat = chat_ref.push(chat_data)  # type: ignore
        return new_chat.key  # type: ignore


    def get_user_chats(self, user_id: int) -> dict[str, Any]:
        """Get all chats for a user"""
        chats = {}

        chat_ref = self.root.child('chats')
        chats.update(chat_ref.order_by_child(
            f'participants/user1_id').equal_to(user_id).get())
        chats.update(chat_ref.order_by_child(
            f'participants/user2_id').equal_to(user_id).get())

        return chats
