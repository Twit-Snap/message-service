from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from models.errors.errors import AuthenticationError, CustomHTTPException, ValidationError


def error_handler(request: Request, e: Exception) -> JSONResponse:
    match e:
        case CustomHTTPException():
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "type": "about:blank",
                    "title": e.title,
                    "status": e.status_code,
                    "detail": e.detail,
                    "instance": str(request.url)
                }
            )

        case HTTPException():
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "type": "about:blank",
                    "title": '',
                    "status": e.status_code,
                    "detail": e.detail,
                    "instance": str(request.url)
                }
            )

        case _:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "type": "about:blank",
                    "title": "Internal server error",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "An unexpected error occurred",
                    "instance": str(request.url)
                }
            )
