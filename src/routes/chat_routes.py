from json import dumps
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from controller.chat_controller import ChatController
from models.chat import ChatBase, Chat
from models.message import MessageBase, Message
from service.chat_service import ChatService
from utils.sendNotification import send_push_notification
from models.jwt import JwtUserPayload

router = APIRouter()


@router.post(
    "",
    summary="Create a chat and get its id",
    status_code=status.HTTP_201_CREATED,
    response_model=Chat
)
def create_chat(chat: ChatBase) -> Chat:
    ChatController().validate_users(chat)

    created_chat = ChatService().create_chat(chat)

    return created_chat


@router.post(
    "/{id}",
    summary="Post a message in the chat {id}",
    status_code=status.HTTP_201_CREATED,
    response_model=Message
)
def send_message(message: MessageBase, request: Request, id: str) -> JSONResponse:
    authUser: JwtUserPayload = request.state.user

    message.content = message.content.strip()

    created_message = ChatService().send_message(
        message,
        authUser["userId"],
        id
    )

    if message.receiver_expo_token:
        send_push_notification(
            message.receiver_expo_token,
            f"{authUser['username']} sent a new message",
            message.content,
            data={
                "type": "message",
                "params": {
                    "id": id,
                    "user": authUser["username"]
                }
            }
        )

    return JSONResponse(dict(created_message), status_code=status.HTTP_201_CREATED)


@router.patch(
    "/{chat_id}/messages/{id}",
    summary="Edit content of chat message",
    status_code=status.HTTP_200_OK,
    response_model=Message
)
def edit_message(message: MessageBase, id: str, chat_id: str, request: Request) -> JSONResponse:
    authUser = request.state.user

    message.content = message.content.strip()

    created_message = ChatService().edit_message(
        message,
        authUser["userId"],
        chat_id,
        id
    )

    return JSONResponse(dict(created_message), status_code=status.HTTP_200_OK)


@router.delete(
    "/{chat_id}/messages/{id}",
    summary="Delete a message",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None
)
def delete_message(id: str, chat_id: str, request: Request) -> None:
    authUser = request.state.user

    ChatService().delete_message(
        authUser["userId"],
        chat_id,
        id
    )
