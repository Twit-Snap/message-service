import logging
from os import environ
import dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

import routes.chat_routes as chat_routes
from middleware.auth_middleware import JWTMiddleware
from middleware.error_handler import error_handler
from starlette.middleware.base import BaseHTTPMiddleware
import firebase_admin
from firebase_admin import credentials, db

app = FastAPI()


@app.exception_handler(HTTPException)
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_handler(request, exc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add JWT middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=JWTMiddleware())


app.include_router(chat_routes.router, prefix="/chats", tags=["chats"])


def init_firebase():
    cred = credentials.Certificate('src/serviceAccountKey.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': environ.get("DATABASE_URL")
    })


if __name__ == "__main__":
    dotenv.load_dotenv(".env")

    init_firebase()

    HOST: str = environ.get("HOST") or "0.0.0.0"
    PORT: int = int(environ.get("PORT") or 8082)

    uvicorn.run(app, host=HOST, port=PORT)
