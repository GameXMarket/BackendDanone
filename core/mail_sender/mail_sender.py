from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import aiosmtplib

from jinja2 import Environment, FileSystemLoader

from core import settings as conf


class AsyncEmailSender:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.server = None

    async def connect(self):
        print("connecting to smtp")
        self.server: aiosmtplib.SMTP = aiosmtplib.SMTP()
        try:
            await self.server.connect(hostname=self.smtp_server, port=self.smtp_port, timeout=5)
        except aiosmtplib.errors.SMTPConnectTimeoutError as e:
            print("Потому нужно будет пофиксить подключени к ssl порту")
            self.smtp_port = conf.SMTP_PORT
            await self.server.connect(hostname=self.smtp_server, port=self.smtp_port, timeout=5)
        try:
            await self.server.starttls()
        except aiosmtplib.errors.SMTPException:
            print("Также нужно будет почитать доки на счёт этого..")
        await self.server.login(self.username, self.password)

    async def send_email(self, sender_name, receiver_email, subject, body):
        if not self.server:
            raise ValueError(f"SMTP server must be {type(aiosmtplib.SMTP)}, not None")
        message = MIMEMultipart("alternative")
        message["From"] = formataddr((str(Header(sender_name, "utf-8")), self.username))
        message["To"] = receiver_email
        message["Subject"] = subject
        message["X-Image-URL"] = "https://avatars.githubusercontent.com/u/151668482"
        message.attach(MIMEText(body, "html"))

        await self.server.sendmail(self.username, receiver_email, message.as_string())

    async def disconnect(self):
        if self.server:
            await self.server.quit()


async def render_auth_template(template_file, data: dict):
    if not data.get("debug"):
        data["debug"] = conf.DEBUG
    
    env = Environment(loader=FileSystemLoader("_locales"), enable_async=True)
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
