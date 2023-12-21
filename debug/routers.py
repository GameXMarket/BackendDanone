import os
import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from core.mail_sender import render_auth_template


current_file_path = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger("uvicorn")
router = APIRouter(tags=["debug"], prefix="/docs")


@router.get("/reset-password")
async def get_password_reset_html(token: str):
    html_string = await render_auth_template(
        template_file="_reset_password.html",
        data={"token": token},
        templates_path=current_file_path,
    )
    return HTMLResponse(content=html_string)


