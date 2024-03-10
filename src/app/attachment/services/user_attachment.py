from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base_attachment import BaseAttachmentManager
from .. import models


class UserAttachmentManager(BaseAttachmentManager):
    async def create_new_attachment(
        self, db_session: AsyncSession, file: UploadFile, user_id: int
    ):
        attachment = models.UserAttachment(author_id=user_id, user_id=user_id)
        db_session.add(attachment)
        await db_session.flush()

        await super().create_new_attachment(db_session, attachment.id, [file])

        return attachment.to_dict()

    async def get_attachment(self, db_session: AsyncSession, user_id: int):
        model = models.UserAttachment
        whereclause = (models.UserAttachment.user_id == user_id)
        return await super().get_attachment(db_session, model, whereclause)
    
    async def get_only_files(self, db_session: AsyncSession, user_id: int):
        # TODO После нужен будет рефакторинг
        # мб стоит перенести в бейс менеджер
        
        _result = []
        base_file_url = "/attacment/getfile/{file_hash}?id={attachment_id}"
        
        stmt = (
            select(models.File.hash, models.File.attachment_id)
            .where(models.UserAttachment.id == models.File.attachment_id)
            .where(models.UserAttachment.user_id == user_id)   
        )
        
        result = (await db_session.execute(stmt)).all()
        
        if not result:
            return None
        
        for file_hash, attachment_id in result:
            _result.append(
                base_file_url.format(file_hash=file_hash, attachment_id=attachment_id)
            )
        
        return _result


user_attachment_manager = UserAttachmentManager()




