import logging

from fastapi import Depends, APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from core import settings as conf
from core.database import get_session
from core.depends import depends as deps
from app.tokens import schemas as schemas_t
from ..services import *


logger = logging.getLogger("uvicorn")
router = APIRouter()
default_session = deps.UserSession()
base_attachment_manager = BaseAttachmentManager()
offer_attacment_manager = OfferAttachmentManager()


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


@router.get("/getfile")
async def get_file_by_id(
    file_id: int,
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    file_path = await base_attachment_manager.get_x_accel_redirect_by_file_id(
        db_session, file_id, user.id, conf.NGINX_DATA_ENDPOINT
    )

    if not file_path:
        raise HTTPException(404)

    response = JSONResponse(
        {"detail": "File found"}, headers={"X-Accel-Redirect": file_path}
    )
    return response


@router.post("/uploadfile/offer/")
async def create_upload_file(
    files: list[UploadFile],
    current_session: tuple[schemas_t.JwtPayload, deps.UserSession] = Depends(
        default_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    token_data, user_context = current_session
    user = await user_context.get_current_active_user(db_session, token_data)

    return await offer_attacment_manager.create_new_attachment(
        db_session, files, user.id
    )
