import logging

from fastapi import Depends, Query, APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from core import settings as conf
from core.utils import setup_helper
from core.database import get_session
from core.depends import depends as deps
from app.tokens import schemas as schemas_t
from ..services import *


logger = logging.getLogger("uvicorn")
router = APIRouter()
default_session = deps.UserSession()
base_attachment_manager = BaseAttachmentManager()
offer_attacment_manager = OfferAttachmentManager()
user_attacment_manager = UserAttachmentManager()
message_attacment_manager = MessageAttachmentManager()
setup_helper.add_new_coroutine_def(base_attachment_manager.setup)

from fastapi import responses

@router.get("/getfile/{file_hash}")
async def get_file_by_hash(
    file_hash: str,
    attachemnt_id: int = Query(alias="id"),
    db_session: AsyncSession = Depends(get_session),
):

    print(attachemnt_id)
    print(file_hash)
    file_path = await base_attachment_manager.get_x_accel_redirect_by_file_hash(
        db_session, file_hash, attachemnt_id, conf.NGINX_DATA_ENDPOINT
    )

    
    print(file_path)
    
    if not file_path:
        raise HTTPException(404)

    response = Response(headers={"X-Accel-Redirect": file_path})
    return response


@router.get("/")
async def get_files_by_attachment_id(
    attachment_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    files = await base_attachment_manager.get_files_by_attacment_id(
        db_session, attachment_id, user.id
    )

    if not files:
        raise HTTPException(404)

    return files


@router.post("/uploadfiles/offer/")
async def create_upload_files_offer(
    files: list[UploadFile],
    offer_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    return await offer_attacment_manager.create_new_attachment(
        db_session, files, user.id, offer_id
    )


@router.post("/uploadfiles/user/")
async def create_upload_files_user(
    file: UploadFile,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    return await user_attacment_manager.create_new_attachment(
        db_session, file, user.id
    )


@router.post("/uploadfiles/message/")
async def create_upload_files_message(
    files: list[UploadFile],
    message_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    return await message_attacment_manager.create_new_attachment(
        db_session, files, user.id, message_id
    )
