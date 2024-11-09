from typing import Literal, TypedDict, Union


class JwtUserPayload(TypedDict):
    type: Literal['user']
    userId: int
    email: str
    username: str


class JwtAdminPayload(TypedDict):
    type: Literal['admin']
    username: str
    email: str


JwtCustomPayload = JwtUserPayload | JwtAdminPayload
