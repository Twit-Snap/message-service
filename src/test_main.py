# test_chat_routes.py
import json
from typing import Any, Coroutine, Literal, Optional, Union
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from unittest.mock import Mock, patch
from datetime import datetime

from controller.chat_controller import ChatController
from middleware.auth_middleware import JWTMiddleware
from middleware.error_handler import error_handler
from models.chat import Chat, ChatBase
from models.message import Message, MessageBase
from models.errors.errors import ValidationError, MessageMaxLengthException
from models.user import User
from repository.firebase_db import FirebaseDB
from routes.chat_routes import router
from starlette.middleware.base import BaseHTTPMiddleware
from service.chat_service import ChatService
from service.jwt_service import JWTService
from models.jwt import JwtCustomPayload
import requests_mock
import dotenv
# Fixtures
from os import getenv
dotenv.load_dotenv()


class MockJWTService(JWTService):
    def __init__(self):
        pass

    def sign(self, payload: JwtCustomPayload) -> str:
        return "test-token"

    def verify(self, token: str) -> Union[dict, str]:
        return {
            "userId": 1, "username": "test", 'email': "test@gmail.com", "type": "user"
        }

    def decode(self, token: str) -> Optional[Union[dict, str]]:
        return {
            "userId": 1, "username": "test", 'email': "test@gmail.com", "type": "user"
        }


class MockHTTPBearer(HTTPBearer):
    def __init__(self):
        pass

    async def __call__(  # type: ignore
        self, request: Request
    ) -> Coroutine[Any, Any, HTTPAuthorizationCredentials | None]:
        return HTTPAuthorizationCredentials(
            # type: ignore
            scheme="Bearer", credentials="test-token"
        )


@pytest.fixture(autouse=True)
def mock_firebase():
    with patch('service.chat_service.FirebaseDB') as mock:
        yield mock


@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer dummy-token"}


@pytest.fixture
def sample_chat_data():
    return {
        "user1": {"id": 1, "username": "test1"},
        "user2": {"id": 2, "username": "test2"}
    }


@pytest.fixture
def sample_message_data():
    return {
        "content": "Hello, World!"
    }


app = FastAPI()

app.add_middleware(BaseHTTPMiddleware,
                   dispatch=JWTMiddleware(MockJWTService(), MockHTTPBearer()))


app.include_router(router, prefix="/chats", tags=["chats"])


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_handler(request, exc)


client = TestClient(app)


# Unit Tests

class TestChatController:
    def test_validate_users_success(self):
        chat = ChatBase(user1=User(id=1, username="test1"),
                        user2=User(id=2, username="test2"))
        # Should not raise any exception
        ChatController().validate_users(chat)

    def test_validate_users_id_failure(self):
        chat = ChatBase(user1=User(id=0, username="test1"),
                        user2=User(id=2, username="test2"))
        with pytest.raises(ValidationError):
            ChatController().validate_users(chat)

    def test_validate_users_username_failure(self):
        chat = ChatBase(user1=User(id=1, username=""),
                        user2=User(id=2, username="test2"))
        with pytest.raises(ValidationError):
            ChatController().validate_users(chat)


class TestChatService:
    def test_validate_message_success(self, mock_firebase):
        mock_instance = mock_firebase.return_value
        service = ChatService(mock_instance)
        # Should not raise any exception
        service.validate_message("Valid message")

    def test_validate_message_too_long(self, mock_firebase):
        mock_instance = mock_firebase.return_value
        service = ChatService(mock_instance)

        with pytest.raises(MessageMaxLengthException):
            service.validate_message("x" * 281)

    def test_create_chat(self, mock_firebase):
        mock_instance = mock_firebase.return_value
        mock_instance.create_chat.return_value = "chat123"

        service = ChatService(mock_instance)
        chat = ChatBase(user1=User(id=1, username="test1"),
                        user2=User(id=2, username="test2"))
        result = service.create_chat(chat)

        assert isinstance(result, Chat)
        assert result.id == "chat123"
        mock_instance.create_chat.assert_called_once_with(
            User(id=1, username="test1"), User(id=2, username="test2"))

    def test_send_message(self, mock_firebase):
        mock_instance = mock_firebase.return_value
        mock_instance.send_message.return_value = {
            "id": "msg123",
            "content": "Hello",
            "sender_id": 1,
            "created_at": datetime.now().isoformat()
        }

        service = ChatService(mock_instance)
        message = MessageBase(content="Hello")
        result = service.send_message(message, 1, "chat123")

        assert isinstance(result, Message)
        assert result.content == "Hello"
        mock_instance.send_message.assert_called_once_with(
            "chat123", 1, "Hello")

# Integration Tests


class TestChatRoutes:
    def test_create_chat_success(self, mock_firebase, sample_chat_data):
        mock_instance = mock_firebase.return_value
        mock_instance.create_chat.return_value = "chat123"

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"id": 1, "username": "test"}
            )

            response = client.post("/chats/", json=sample_chat_data)

            assert response.status_code == 201
            assert response.json()["id"] == "chat123"

    def test_create_chat_validation_error(self):
        invalid_data = {
            "user1_id": 1
            # missing user2_id
        }

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"id": 1, "username": "test"}
            )

            response = client.post("/chats/", json=invalid_data)
            assert response.status_code == 422  # Validation error

    def test_send_message_success(self, mock_firebase, sample_message_data):
        mock_instance = mock_firebase.return_value
        mock_instance.send_message.return_value = {
            "id": "msg123",
            "content": sample_message_data["content"],
            "sender_id": 1,
            "created_at": datetime.now().isoformat()
        }

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"id": 1, "username": "test"}
            )

            response = client.post(
                "/chats/chat123",
                json=sample_message_data
            )

            assert response.status_code == 201
            assert response.json()["content"] == sample_message_data["content"]

    def test_edit_message_success(self, mock_firebase, sample_message_data):
        mock_instance = mock_firebase.return_value
        mock_instance.edit_message.return_value = {
            "id": "msg123",
            "content": "Updated content",
            "sender_id": 1,
            "created_at": datetime.now().isoformat(),
            "edited_at": datetime.now().isoformat()
        }

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"id": 1, "username": "test"}
            )

            response = client.patch(
                "/chats/chat123/messages/msg123",
                json={"content": "Updated content"}
            )

            assert response.status_code == 200
            assert response.json()["content"] == "Updated content"

    def test_delete_message_success(self, mock_firebase):
        mock_instance = mock_firebase.return_value

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"id": 1, "username": "test"}
            )

            response = client.delete("/chats/chat123/messages/msg123")

            assert response.status_code == 204
            mock_instance.delete_message.assert_called_once_with(
                "chat123", "msg123", 1
            )


# Error handling tests


class TestAuthentication:
    def test_invalid_auth_user_username(self):
        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"title": "Invalid username",
                      "detail": "Invalid username provided"},
                status_code=400
            )

            with pytest.raises(Exception):
                response = client.post(
                    "/chats/test-chat-id",
                    json={"content": "Hello"}
                )

                data = response.json()

                assert response.status_code == 400
                assert data.detail == "Invalid username provided"
                assert data.title == "Invalid username"

    def test_auth_user_blocked(self):
        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"title": "User blocked",
                      "detail": "Blocked error"},
                status_code=403
            )

            with pytest.raises(Exception):
                response = client.post(
                    "/chats/test-chat-id",
                    json={"content": "Hello"}
                )

                data = response.json()

                assert response.status_code == 403
                assert data.detail == "Blocked error"
                assert data.title == "User blocked"

    def test_auth_user_unauthorized(self):
        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"title": "AuthenticationError",
                      "detail": ""},
                status_code=401
            )

            with pytest.raises(Exception):
                response = client.post(
                    "/chats/test-chat-id",
                    json={"content": "Hello"}
                )

                data = response.json()

                assert response.status_code == 401
                assert data.detail == ""
                assert data.title == "AuthenticationError"

    def test_auth_user_not_found(self):
        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"title": "NotFoundError",
                      "detail": "username test not found"},
                status_code=404
            )

            with pytest.raises(Exception):
                response = client.post(
                    "/chats/test-chat-id",
                    json={"content": "Hello"}
                )

                data = response.json()

                assert response.status_code == 404
                assert data.detail == "username test not found"
                assert data.title == "NotFoundError"

    def test_service_unavailable(self):
        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"title": "ServiceUnavailableError",
                      "detail": "Service unavailable"},
                status_code=500
            )

            with pytest.raises(Exception):
                response = client.post(
                    "/chats/test-chat-id",
                    json={"content": "Hello"}
                )

                data = response.json()

                assert response.status_code == 500
                assert data.detail == "Service unavailable"
                assert data.title == "ServiceUnavailableError"

    def test_no_token(self):
        class MockHTTPBearer(HTTPBearer):
            def __init__(self):
                pass

            async def __call__(  # type: ignore
                self, request: Request
            ) -> Coroutine[Any, Any, HTTPAuthorizationCredentials | None]:
                return None  # type: ignore

        app_aux = FastAPI()

        app_aux.add_middleware(BaseHTTPMiddleware,
                               dispatch=JWTMiddleware(MockJWTService(), MockHTTPBearer()))

        app_aux.include_router(router, prefix="/chats", tags=["chats"])

        @app_aux.exception_handler(Exception)
        async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
            return error_handler(request, exc)

        client_aux = TestClient(app_aux)

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"title": "AuthenticationError",
                      "detail": ""},
                status_code=401
            )

            with pytest.raises(Exception):
                response = client_aux.post(
                    "/chats/test-chat-id",
                    json={"content": "Hello"}
                )

                data = response.json()

                assert response.status_code == 401
                assert data.detail == ""
                assert data.title == "AuthenticationError"


class TestErrorHandling:
    def test_message_too_long(self, mock_firebase):
        long_message = {"content": "x" * 281}

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"id": 1, "username": "test"}
            )

            response = client.post(
                "/chats/chat123",
                json=long_message
            )

            assert response.status_code == 400

    def test_invalid_chat_id(self, mock_firebase):
        mock_instance = mock_firebase.return_value
        mock_instance.send_message.side_effect = Exception("Chat not found")

        with requests_mock.Mocker() as m:
            m.get(
                f"{getenv('USERS_SERVICE_URL')}/users/test",
                json={"id": 1, "username": "test"}
            )

            with pytest.raises(Exception):
                response = client.post(
                    "/chats/invalid_chat_id",
                    json={"content": "Hello"}
                )

                assert response.status_code == 404
