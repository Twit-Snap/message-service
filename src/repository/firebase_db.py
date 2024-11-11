import datetime
from re import S
from typing import Any
from os import getenv
from json import dumps
from firebase_admin import db

from models.errors.errors import AuthenticationError, NotFoundError
from models.user import User


class FirebaseDB:
    def __init__(self):
        """Initialize Firebase connection"""
        self.root = db.reference('/')

    def _set_chat_updated_at(self, chat_id: str, user_id: int, timestamp: str | None = None):
        chat_ref = self.root.child("chats").child(chat_id)

        chat_value = chat_ref.get()

        if not chat_value:
            raise NotFoundError("Chat not found")

        if chat_value["participants"]["user1"]["id"] != user_id and chat_value["participants"]["user2"]["id"] != user_id:  # type: ignore
            raise AuthenticationError(
                "To update a chat you must be in it"
            )

        chat_value.update(  # type: ignore
            {"updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat() if not timestamp else timestamp})  # type: ignore

        chat_ref.set(chat_value)

    def _validate_sender(self, message_ref: db.Reference, user_id: int):
        original_sender = message_ref.child('sender_id').get()

        if not original_sender:
            raise NotFoundError("Message not found")

        elif original_sender != user_id:
            raise AuthenticationError(
                "To update a message you must be the same user"
            )

    def edit_message(self, chat_id: str, message_id: str, new_message: str, user_id: int) -> dict:

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self._set_chat_updated_at(chat_id, user_id,  timestamp)

        message_ref = self.root.child(
            'messages').child(chat_id).child(message_id)

        self._validate_sender(message_ref, user_id)

        message_ref.update({
            "content": new_message,
            "edited_at": timestamp
        })

        message = message_ref.get()

        return {
            'id': message_id,
            **message  # type: ignore
        }

    def delete_message(self, chat_id: str, message_id: str, user_id: int) -> None:

        self._set_chat_updated_at(chat_id, user_id)

        message_ref = self.root.child(
            'messages').child(chat_id).child(message_id)

        self._validate_sender(message_ref, user_id)

        message_ref.delete()

    def send_message(self, chat_id: str, user_id: int, message: str) -> dict:
        """Send a message in a chat"""
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self._set_chat_updated_at(chat_id, user_id, timestamp)

        messages_ref = self.root.child('messages').child(chat_id)
        message_data = {
            'content': message,
            'sender_id': user_id,
            'created_at': timestamp
        }

        new_message = messages_ref.push(message_data)  # type: ignore

        return {
            'id': new_message.key,
            **message_data
        }

    def __chat_exist(self, user1: User, user2: User) -> str:
        chats: dict[str, Any] = self.get_user_chats(user1.id)

        min_user = user1 if user1.id < user2.id else user2
        max_user = user1 if user1.id > user2.id else user2

        participants: dict = {
            "user1": dict(min_user),
            "user2": dict(max_user)
        }

        for key, chat in chats.items():
            if chat["participants"] == participants:
                return key

        return ''

    def create_chat(self, user1: User, user2: User) -> str:
        """Create a new chat between two users"""
        existent_chat_key = self.__chat_exist(user1, user2)

        if len(existent_chat_key) > 0:
            # paticipants_ref = self.root.child('chats').child(
            #     existent_chat_key).child("participants")
            # participants = paticipants_ref.get()

            # print(participants)

            # if participants["user1"]["username"] != min_user.username:  # type: ignore
            #     paticipants_ref.child("user1").update(dict(min_user))

            # elif participants["user2"]["username"] != max_user.username:  # type: ignore
            #     paticipants_ref.child("user2").update(dict(max_user))

            return existent_chat_key

        min_user = user1 if user1.id < user2.id else user2
        max_user = user1 if user1.id > user2.id else user2

        chat_ref = self.root.child('chats')

        chat_data = {
            'participants': {
                "user1": dict(min_user),
                "user2": dict(max_user)
            },
            'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        new_chat = chat_ref.push(chat_data)  # type: ignore
        return new_chat.key  # type: ignore

    def get_user_chats(self, user_id: int) -> dict[str, Any]:
        """Get all chats for a user"""
        chats = {}

        chat_ref = self.root.child('chats')
        chats.update(chat_ref.order_by_child(
            f'participants/user1/id').equal_to(user_id).get())
        chats.update(chat_ref.order_by_child(
            f'participants/user2/id').equal_to(user_id).get())

        return chats
