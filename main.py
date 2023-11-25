import json
import asyncio

import uvicorn
from fastapi import FastAPI

import core.configuration as conf
from core.database import init_models
from api import api_router


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

app.include_router(api_router)

if __name__ == "__main__":
    asyncio.run(init_models(drop_all=False))
    uvicorn.run("main:app", host=conf.SERVER_IP, port=conf.SERVER_PORT, reload=True)
