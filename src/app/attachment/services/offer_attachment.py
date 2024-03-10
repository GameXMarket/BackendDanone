from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from .base_attachment import BaseAttachmentManager
from .. import models


class OfferAttachmentManager(BaseAttachmentManager):
    async def create_new_attachment(
        self, db_session: AsyncSession, files: list[UploadFile], user_id: int, offer_id: int
    ):
        attachment = models.OfferAttachment(author_id=user_id, offer_id=offer_id)
        db_session.add(attachment)
        await db_session.flush()

        await super().create_new_attachment(db_session, attachment.id, files)

        return attachment.to_dict()

    async def get_attachment(self, db_session: AsyncSession, offer_id: int):
        model = models.OfferAttachment
        whereclause = (models.OfferAttachment.offer_id == offer_id)
        return await super().get_attachment(db_session, model, whereclause)


offer_attachment_manager = OfferAttachmentManager()







