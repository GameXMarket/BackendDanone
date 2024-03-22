from typing import Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.settings import BASE_FILE_URL
from .base_attachment import BaseAttachmentManager
from .. import models


class CategoryValueAttachmentManager(BaseAttachmentManager):
    async def create_new_attachment(
        self, db_session: AsyncSession, files: list[UploadFile], user_id: int, category_value_id: int
    ):
        attachment = models.CategoryValueAttachemnt(author_id=user_id, category_value_id=category_value_id)
        db_session.add(attachment)
        await db_session.flush()

        await super().create_new_attachment(db_session, attachment.id, files)

        return attachment.to_dict()
    
    async def get_attachment(self, db_session: AsyncSession, category_value_id: int):
        model = models.CategoryValueAttachemnt
        whereclause = (models.CategoryValueAttachemnt.category_value_id == category_value_id)
        return await super().get_attachment(db_session, model, whereclause)

    async def get_only_files(self, db_session: AsyncSession, category_value_id: int):
        # TODO После возможно нужен будет рефакторинг
        # мб стоит перенести в бейс менеджер
        
        _result = []
        
        stmt = (
            select(models.File.hash, models.File.attachment_id)
            .where(models.CategoryValueAttachemnt.id == models.File.attachment_id)
            .where(models.CategoryValueAttachemnt.category_value_id == category_value_id)
        )
        
        result = (await db_session.execute(stmt)).all()
        
        if not result:
            return None
        
        for file_hash, attachment_id in result:
            _result.append(
                BASE_FILE_URL.format(file_hash=file_hash, attachment_id=attachment_id)
            )
        
        return _result

category_value_attachment_manager = CategoryValueAttachmentManager()
