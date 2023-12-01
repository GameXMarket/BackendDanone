from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import aiosmtplib

from jinja2 import Environment, FileSystemLoader


class AsyncEmailSender:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.server = None

    async def connect(self):
        self.server: aiosmtplib.SMTP = await aiosmtplib.SMTP(
            self.smtp_server, self.smtp_port
        )
        await self.server.starttls()
        await self.server.login(self.username, self.password)

    async def send_email(self, sender_name, receiver_email, subject, body):
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


async def render_auth_template(template_file, token):
    template_dir = "./_locales"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)
    rendered_html = await template.render_async({"token": token})

    return rendered_html
