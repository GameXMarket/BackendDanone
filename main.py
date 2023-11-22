import json

import uvicorn
from fastapi import FastAPI

from database import Base, engine
import configuration as conf


ROUTETRS = []

Base.metadata.create_all(bind=engine)
openapi_tags = json.loads(open("_locales/tags_metadata.json", "r").read())
app = FastAPI(
    debug=conf.DEBUG,
    version="0.1.0" if conf.DEBUG else None,
    title="DanoneMarket" if conf.DEBUG else None,
    summary="DanoneMarket private docs" if conf.DEBUG else None,
    openapi_tags=openapi_tags if conf.DEBUG else None,
    openapi_url="/control/openapi.json" if conf.DEBUG else None,
    docs_url="/control/docs" if conf.DEBUG else None,
    redoc_url=None,
)

for part in ROUTETRS:
    app.include_router(part.router)

if __name__ == "__main__":
    uvicorn.run("server:app", host=conf.SERVER_IP, port=conf.SERVER_PORT, reload=True)
