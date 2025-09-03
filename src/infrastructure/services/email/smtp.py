import smtplib
from email.mime.base import MIMEBase

from src.infrastructure.services.email.send import EmailSender


class SMTPSender(EmailSender):
    def __init__(
        self,
        smtp_server: str | None,
        port: str | None,
        username: str | None,
        password: str | None,
    ):
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password

    def send(self, from_email: str, to: str, email: MIMEBase):
        if self.smtp_server is None or self.port is None:
            raise
        with smtplib.SMTP(host=self.smtp_server, port=int(self.port)) as smtp:
            smtp.login(self.username, self.password)
            smtp.send_message(email, from_addr=from_email, to_addrs=to)
