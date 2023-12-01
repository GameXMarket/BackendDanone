import json
import secrets
import asyncio
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

import core.configuration as conf
from core.database import init_models
from api import api_router


conf.DEBUG = True
security = HTTPBasic()
openapi_tags = json.loads(open("_locales/tags_metadata.json", "r").read())
app = FastAPI(
    debug=conf.DEBUG,
    root_path="" if conf.DEBUG else "/api",
    version=conf.VERSION if conf.DEBUG else None,
    title=conf.TITLE if conf.DEBUG else None,
    summary=conf.SUMMARY if conf.DEBUG else None,
    openapi_tags=openapi_tags if conf.DEBUG else None,
    openapi_url="/openapi.json" if conf.DEBUG else None,
    docs_url="/docs" if conf.DEBUG else None,
    redoc_url=None,
)


def __temp_get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"user"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"password"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(
    username: str = Depends(__temp_get_current_username),
):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(username: str = Depends(__temp_get_current_username)):
    return get_redoc_html(openapi_url="/openapi.json", title="docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(__temp_get_current_username)):
    return get_openapi(title=conf.TITLE, version=conf.VERSION, routes=app.routes)


app.include_router(api_router)


if __name__ == "__main__":
    asyncio.run(init_models(drop_all=True))
    uvicorn.run("main:app", host=conf.SERVER_IP, port=conf.SERVER_PORT, reload=True)
