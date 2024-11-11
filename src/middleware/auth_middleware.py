from os import getenv
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from models.errors.errors import AuthenticationError, BlockedError, NotFoundError, ServiceUnavailableError, ValidationError
from models.jwt import JwtCustomPayload
from service.jwt_service import JWTService
import requests
import logging


class JWTMiddleware:
    def __init__(self, jwt_service: JWTService | None = None, security: HTTPBearer | None = None):
        self.jwt_service = jwt_service or JWTService()
        self.security = security or HTTPBearer()

    async def __call__(self, request: Request, call_next):
        try:
            print(str(request.headers))
            credentials: HTTPAuthorizationCredentials | None = await self.security(request)

            if not credentials:
                raise AuthenticationError()

            token = credentials.credentials
            payload = self.jwt_service.verify(token)

            await self._check_blocked(payload, token)  # type: ignore

            request.state.user = payload
            response = await call_next(request)
            return response

        except HTTPException as e:
            logging.error(str(e))
            raise AuthenticationError()

    async def _check_blocked(self, decodedToken: JwtCustomPayload, token: str) -> None:
        if decodedToken["type"] == 'admin':
            return

        response = requests.get(
            f"{getenv('USERS_SERVICE_URL')}/users/{decodedToken['username']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()

        match response.status_code:
            case 400:
                raise ValidationError(
                    title=data["title"],
                    detail=data["detail"]
                )
            case 401:
                raise AuthenticationError()
            case 403:
                raise BlockedError()
            case 404:
                raise NotFoundError(
                    f'username {decodedToken["username"]} not found')
            case 500:
                raise ServiceUnavailableError()
