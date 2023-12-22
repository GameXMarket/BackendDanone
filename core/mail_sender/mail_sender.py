from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import logging
import os

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from core import settings as conf


logger = logging.getLogger("uvicorn")
current_file_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
locales_path = os.path.join(os.path.dirname(current_file_path), "_locales")


class AsyncEmailSender:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.server = None

    async def connect(self):
        logger.info("Connecting to smtp...")
        self.server: aiosmtplib.SMTP = aiosmtplib.SMTP()
        await self.server.connect(hostname=self.smtp_server, port=self.smtp_port, use_tls=True, timeout=2)
        await self.server.login(self.username, self.password)

    async def send_email(self, sender_name, receiver_email, subject, body):
        if not self.server:
            raise ValueError(f"SMTP server must be {type(aiosmtplib.SMTP)}, not N+one")
        message = MIMEMultipart("alternative")
        message["From"] = formataddr((str(Header(sender_name, "utf-8")), self.username))
        message["To"] = receiver_email
        message["Subject"] = subject
        message["X-Image-URL"] = "https://avatars.githubusercontent.com/u/151668482"
        message.attach(MIMEText(body, "html"))

        await self.server.sendmail(self.username, receiver_email, message.as_string())

    async def disconnect(self):
        if self.server.is_connected:
            await self.server.quit()


async def render_auth_template(template_file, data: dict, **kwargs):
    if not data.get("debug"):
        data["debug"] = conf.DEBUG
    
    # Используется для дебага, чтобы изменить директорию для поиска файлов
    if not (path := kwargs.get("templates_path")):
        env = Environment(loader=FileSystemLoader(locales_path), enable_async=True)
    else:
        env = Environment(loader=FileSystemLoader(path), enable_async=True)
        
    template = env.get_template(template_file)
    rendered_html = await template.render_async(data)

    return rendered_html


user_auth_sender = AsyncEmailSender(
    conf.SMTP_ADRESS,
    conf.SMTP_PORT if conf.DEBUG else conf.SMTP_SSL_PORT,
    conf.USER_VERIFY_LOGIN,
    conf.USER_VERIFY_PASSWORD,
)

password_reset_sender = AsyncEmailSender(
    conf.SMTP_ADRESS,
    conf.SMTP_PORT if conf.DEBUG else conf.SMTP_SSL_PORT,
    conf.PASSWORD_RESET_LOGIN,
    conf.PASSWORD_RESET_PASSWORD,
)
