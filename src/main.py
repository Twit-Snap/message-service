import base64
import json
import logging
from os import getenv
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

import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

app = FastAPI()


@app.middleware("http")
async def add_new_relic_transaction(request, call_next):
    transaction = newrelic.agent.current_transaction()
    if transaction:
        newrelic.agent.set_transaction_name(
            f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


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
    try:
        cred = credentials.Certificate('src/serviceAccountKey.json')

    except:
        cred = credentials.Certificate(json.loads(
            base64.b64decode(getenv("SERVICE_ACCOUNT_KEY")).decode('utf-8')))  # type: ignore

    firebase_admin.initialize_app(cred, {
        'databaseURL': getenv("DATABASE_URL")
    })

    logging.info("Firebase initialized")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s - %(asctime)s', filename='logs.log')

    dotenv.load_dotenv()

    init_firebase()

    HOST: str = getenv("HOST") or "0.0.0.0"
    PORT: int = int(getenv("PORT") or 8082)

    uvicorn.run(app, host=HOST, port=PORT)
