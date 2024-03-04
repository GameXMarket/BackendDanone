from datetime import datetime
from typing import Literal
from urllib.parse import urljoin
import hashlib
import time

from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_
import os, aiofiles, aiofiles.os


from .. import models, schemas
from core.settings import config
from core.utils import check_dir_exists


class FileManager:
    # TODO Зачистка лишних метаданных
    file_delete_mode: Literal[
        "instantly",
        "deferred",
        "manual"
    ] = ...
    """
     - instantly - Удаление по ивенту 
     - deferred - Отложенное в определённый момент
     - manual - Ручной запуск скрипта для очистки
    """
    async def _write_file(self, file_data: bytes, file_name: str):
        current_data = datetime.now()
        unix_timestamp = int(time.mktime(current_data.date().timetuple()))
        file_dir_path = os.path.join(
            config.DATA_PATH, str(unix_timestamp), str(current_data.hour)
        )
        await check_dir_exists(file_dir_path, auto_create=True)

        file_path = os.path.join(file_dir_path, file_name)

        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(file_data)

    async def _delete_file(self, path_to_file: str):
        await aiofiles.os.remove(path_to_file)

        dir_path = os.path.dirname(path_to_file)
        files_in_dir = await aiofiles.os.listdir(dir_path)

        if not files_in_dir:
            await aiofiles.os.rmdir(dir_path)

    async def _read_file(self, path_to_file: str):
        async with aiofiles.open(path_to_file, "r") as f:
            content = await f.read()

        return content

    async def _get_created_at_by_hash(
        self, db_session: AsyncSession, md5hash: str
    ) -> int:
        stmt = select(models.File.created_at).where(models.File.hash == md5hash)
        date = (await db_session.execute(stmt)).first()
        if date:
            return date[0]

        return None

    async def _get_path_by_file_id(self, db_session: AsyncSession, file_id: int, user_id: int) -> str:
        stmt = (
            select(models.File.created_at, models.File.hash)
            .where(models.File.id == file_id)
            .where(models.Attachment.id == models.File.attachment_id)
            .where(models.Attachment.author_id == user_id)

        )
        result = (await db_session.execute(stmt)).fetchone()
        
        if result:
            unix_time, file_hash = result
            timestamp_data = datetime.fromtimestamp(unix_time)
            unix_timestamp = int(time.mktime(timestamp_data.date().timetuple()))
            return f"/{unix_timestamp}/{timestamp_data.hour}/{file_hash}"

        return None


class BaseAttachmentManager(FileManager):
    """
    Есть вероятность использования Depends
    Не использовать внутреннее состояние
    """

    def __init__(self) -> None:
        pass

    def _get_hash_md5(self, file_data: bytes):
        return hashlib.md5(file_data).hexdigest()

    async def create_new_attachment(
        self, db_session: AsyncSession, attachment_id: int, files: list[UploadFile]
    ):
        for file in files:
            file_data = await file.read()
            file_hash = self._get_hash_md5(file_data)
            exist_file_data = await self._get_created_at_by_hash(db_session, file_hash)
            file_created = exist_file_data if exist_file_data else int(time.time())

            file_metadata = models.File(
                attachment_id=attachment_id,
                hash=file_hash,
                name=file.filename,
                created_at=file_created,
            )
            db_session.add(file_metadata)

            if not exist_file_data:
                await self._write_file(file_data, file_hash)

        await db_session.commit()

    async def get_files_by_attacment_id(
        self, db_session: AsyncSession, attachment_id: int, user_id: int
    ):
        stmt = (
            select(models.File)
            .where(models.File.attachment_id == attachment_id)
            .where(models.Attachment.id == models.File.attachment_id)
            .where(models.Attachment.author_id == user_id)
        )
        files = (await db_session.execute(stmt)).scalars().all()
        return files

    async def get_x_accel_redirect_by_file_id(
        self,
        db_session: AsyncSession,
        file_id: int,
        user_id: int,
        nginx_data_endpoint: str,
    ):
        in_data_path = await self._get_path_by_file_id(db_session, file_id, user_id)

        if not in_data_path:
            return None

        file_x_accel_redirect_path = nginx_data_endpoint + in_data_path
        return file_x_accel_redirect_path


class OfferAttachmentManager(BaseAttachmentManager):
    async def create_new_attachment(
        self, db_session: AsyncSession, files: list[UploadFile], user_id: int
    ):
        attachment = models.OfferAttachment(author_id=user_id)
        db_session.add(attachment)
        await db_session.flush()

        await super().create_new_attachment(db_session, attachment.id, files)

        return attachment.to_dict()


class UserAttachmentManager(BaseAttachmentManager):

    ...


class MessageAttachmentManager(BaseAttachmentManager):

    ...


"""
class ConflictAttacmentManager(BaseAttacmentManager):
    ...
"""
