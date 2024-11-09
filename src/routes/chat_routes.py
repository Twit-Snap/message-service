from json import dumps
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from controller.chat_controller import ChatController
from models.chat import ChatBase, Chat
from models.message import MessageBase, Message
from service.chat_service import ChatService

router = APIRouter()


@router.post("/", summary="Create a chat and get its id", status_code=status.HTTP_201_CREATED)
def create_chat(chat: ChatBase) -> JSONResponse:
    print("Created")
    ChatController().validate_users(chat)

    created_chat = ChatService().create_chat(chat)
    return JSONResponse(dict((created_chat)))


@router.post("/{id}", summary="Post a message in the chat {id}", status_code=status.HTTP_201_CREATED)
def send_message(message: MessageBase, request: Request, id: str) -> JSONResponse:
    authUser = request.state.user

    created_message = ChatService().send_message(
        message,
        authUser["userId"],
        id
    )

    return JSONResponse(dict(created_message))
