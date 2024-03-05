from datetime import datetime
from typing import Literal
from urllib.parse import urljoin
import hashlib
import time
import json

from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, and_
import os, aiofiles, aiofiles.os


from .. import models, schemas
from core.settings import config
from core.utils import check_dir_exists
from core.database import event_listener, context_get_session


class FileManager:
    # TODO Зачистка лишних метаданных
    # TODO Требуется настроить очередь для выполнения отложенного выполнения
    file_delete_mode: Literal[
        "instantly",
        "deferred",
        "manual"
    ] = config.FILES_DELETE_MODE
    """
     - instantly - Удаление по ивенту 
     - deferred - Отложенное в определённый момент
     - manual - Ручной запуск скрипта для очистки
    """
    async def setup(self):
        await event_listener.add_listener("new_deleted_file", self.file_delete_callback)
    
    def _get_hash_md5(self, file_data: bytes):
        return hashlib.md5(file_data).hexdigest()
    
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
        path_to_file = os.path.join(config.DATA_PATH, path_to_file)
        
        await aiofiles.os.remove(path_to_file)

        # TODO вероятно временно на время отладки (для удобства)
        dir_path = os.path.dirname(path_to_file)
        files_in_dir = await aiofiles.os.listdir(dir_path)

        if not files_in_dir:
            await aiofiles.os.rmdir(dir_path)

    async def _read_file(self, path_to_file: str):
        async with aiofiles.open(path_to_file, "r") as f:
            content = await f.read()

        return content

    def _get_file_path_by_unix_hash(self, unix: str, hash: str):
        timestamp_data = datetime.fromtimestamp(unix)
        unix_timestamp = int(time.mktime(timestamp_data.date().timetuple()))
        return f"{unix_timestamp}/{timestamp_data.hour}/{hash}"
    
    async def _get_created_at_by_hash(
        self, db_session: AsyncSession, md5hash: str
    ) -> int:
        stmt = select(models.File.created_at).where(models.File.hash == md5hash)
        date = (await db_session.execute(stmt)).first()
        if date:
            return date[0]

        return None

    async def _get_unix_hash_by_file_id(self, db_session: AsyncSession, file_id: int, user_id: int) -> str:
        stmt = (
            select(models.File.created_at, models.File.hash)
            .where(models.File.id == file_id)
            .where(models.Attachment.id == models.File.attachment_id)
            .where(models.Attachment.author_id == user_id)

        )
        result = (await db_session.execute(stmt)).fetchone()
        
        if not result:
            return None

        return result
    
    async def file_delete_callback(self, _, __, ___, payload: str):       
        if self.file_delete_mode != "instantly":
            return
        
        file_delete_data: dict = json.loads(payload)
        file_path = self._get_file_path_by_unix_hash(**file_delete_data)
        await self._delete_file(file_path)

        stmt = delete(models.DeletedFile).where(models.DeletedFile.hash == file_delete_data["hash"])
        async with context_get_session() as db_session:
            await db_session.execute(stmt)


class BaseAttachmentManager(FileManager):
    """
    Есть вероятность использования Depends
    Не использовать внутреннее состояние
    """

    def __init__(self) -> None:
        pass

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
        unix_hash = await self._get_unix_hash_by_file_id(db_session, file_id, user_id)
        
        if not unix_hash:
            return None
        
        in_data_path =  '/' + self._get_file_path_by_unix_hash(*unix_hash)
        file_x_accel_redirect_path = nginx_data_endpoint + in_data_path
        return file_x_accel_redirect_path


class OfferAttachmentManager(BaseAttachmentManager):
    async def create_new_attachment(
        self, db_session: AsyncSession, files: list[UploadFile], user_id: int, offer_id: int
    ):
        attachment = models.OfferAttachment(author_id=user_id, offer_id=offer_id)
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
