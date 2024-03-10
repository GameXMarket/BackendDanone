from typing import Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base_attachment import BaseAttachmentManager
from .. import models


class MessageAttachmentManager(BaseAttachmentManager):
    async def create_new_attachment(
        self, db_session: AsyncSession, files: list[UploadFile], user_id: int, message_id: int
    ):
        attachment = models.MessageAttachment(author_id=user_id, message_id=message_id)
        db_session.add(attachment)
        await db_session.flush()

        await super().create_new_attachment(db_session, attachment.id, files)

        return attachment.to_dict()
    
    async def get_attachment(self, db_session: AsyncSession, message_id: int):
        model = models.MessageAttachment
        whereclause = (models.MessageAttachment.message_id == message_id)
        return await super().get_attachment(db_session, model, whereclause)

message_attachment_manager = MessageAttachmentManager()