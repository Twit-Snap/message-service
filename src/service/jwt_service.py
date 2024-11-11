from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from os import getenv
from typing import Optional, Union

import jwt

from models.errors.errors import AuthenticationError
from models.jwt import JwtCustomPayload


class IJWTService(ABC):
    @abstractmethod
    def sign(self, payload: JwtCustomPayload) -> str:
        pass

    @abstractmethod
    def verify(self, token: str) -> Union[dict, str]:
        pass

    @abstractmethod
    def decode(self, token: str) -> Optional[Union[dict, str]]:
        pass

# JWT Service implementation


class JWTService(IJWTService):
    def __init__(self):
        self.expires_in = timedelta(days=365)
        key = getenv('JWT_SECRET_KEY')
        self.secret: str = key if key else "mySup3rStr0ngDevSecretKey"

        if not self.secret:
            raise ValueError("JWT_SECRET_KEY environment variable is not set")

        logging.info("JWT_SECRET_KEY set")

    def sign(self, payload: JwtCustomPayload) -> str:
        """
        Sign a JWT token with the given payload

        Args:
            payload: The payload to encode in the JWT

        Returns:
            str: The signed JWT token
        """
        expiration = datetime.now() + self.expires_in
        payload_with_exp = {**payload, 'exp': expiration}
        return jwt.encode(payload_with_exp, self.secret, algorithm='HS256')

    def verify(self, token: str) -> Union[dict, str]:
        """
        Verify a JWT token

        Args:
            token: The JWT token to verify

        Returns:
            Union[dict, str]: The decoded payload if valid

        Raises:
            AuthenticationError: If the token is invalid or expired
        """
        try:
            return jwt.decode(token, self.secret, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            raise AuthenticationError()

    def decode(self, token: str) -> Optional[Union[dict, str]]:
        """
        Decode a JWT token without verification

        Args:
            token: The JWT token to decode

        Returns:
            Optional[Union[dict, str]]: The decoded payload or None if invalid
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError:
            return None
