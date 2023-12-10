from sqlalchemy.ext.asyncio import create_async_engine

from core.database import Base
import core.settings.config as conf


engine = create_async_engine(conf.DATABASE_URL, echo=True)


async def init_models(*, drop_all=False):
    if not conf.DEBUG and drop_all:
        raise ValueError("This action is possible only when the debug is enabled!")

    async with engine.begin() as conn:
        if drop_all:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("init models")
