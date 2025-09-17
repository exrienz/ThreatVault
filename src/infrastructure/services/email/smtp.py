import smtplib
from email.mime.base import MIMEBase
from urllib.parse import urlparse

import socks

from src.infrastructure.services.email.send import EmailSender


class SMTPSender(EmailSender):
    def __init__(
        self,
        smtp_server: str | None,
        port: str | None,
        username: str | None,
        password: str | None,
        proxy_mounts: dict | None,
    ):
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
        self.proxy_mounts = proxy_mounts

    def send(self, from_email: str, to: str, email: MIMEBase):
        if self.smtp_server is None or self.port is None:
            raise

        server_url = urlparse(self.smtp_server)
        proxy_url = None
        if self.proxy_mounts:
            proxy = self.proxy_mounts.get(server_url.scheme)
            if proxy:
                proxy_url = urlparse(proxy)
        if proxy_url:
            socks.set_default_proxy(
                socks.PROXY_TYPE_SOCKS4, proxy_url.hostname, proxy_url.port
            )
            socks.wrap_module(smtplib)
        with smtplib.SMTP(host=self.smtp_server, port=int(self.port)) as smtp:
            smtp.login(self.username, self.password)
            smtp.send_message(email, from_addr=from_email, to_addrs=to)
