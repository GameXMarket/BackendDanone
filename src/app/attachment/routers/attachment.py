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
from .. import services


logger = logging.getLogger("uvicorn")
router = APIRouter()
default_session = deps.UserSession()
base_attachment_manager = services.BaseAttachmentManager()
setup_helper.add_new_coroutine_def(base_attachment_manager.setup)


@router.get("/getfile/{file_hash}")
async def get_file_by_hash(
    file_hash: str,
    attachemnt_id: int = Query(alias="id"),
    db_session: AsyncSession = Depends(get_session),
):
    # Несколько странное решение как по мне (сохранить менеджмент статических ссылок)
    # После возможно нужно будет переделать, не думаю, что станет большой проблемой
    file_path = await base_attachment_manager.get_x_accel_redirect_by_file_hash(
        db_session, file_hash, attachemnt_id, conf.NGINX_DATA_ENDPOINT
    )
    
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

    return await services.offer_attachment_manager.create_new_attachment(
        db_session, files, user.id, offer_id
    )


@router.delete("/deletefiles/offer/")
async def delete_offer_attachment(
    offer_id: int = Query(alias="id"),
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    return await services.offer_attachment_manager.delete_attachment_by_offer_id(
        db_session, user.id, offer_id
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

    return await services.user_attachment_manager.create_new_attachment(
        db_session, file, user.id
    )


@router.delete("/deletefiles/user/")
async def delete_user_attachment(
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    return await services.user_attachment_manager.delete_attachment_by_user_id(
        db_session, user.id
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

    return await services.message_attachment_manager.create_new_attachment(
        db_session, files, user.id, message_id
    )


@router.post("/uploadfiles/category_value/")
async def create_upload_files_category_value(
    file: UploadFile,
    category_value_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)
    if not user.is_admin():
        raise HTTPException(403)

    return await services.category_value_attachment_manager.create_new_attachment(
        db_session, file, user.id, category_value_id
    )


@router.delete("/deletefiles/category_value/")
async def delete_category_value_attachment(
    category_value_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)
    if not user.is_admin():
        raise HTTPException(403)

    return await services.category_value_attachment_manager.delete_attachment_by_category_value_id(
        db_session, category_value_id
    )