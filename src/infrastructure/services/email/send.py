from abc import ABC, abstractmethod
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender(ABC):
    @abstractmethod
    def send(self, from_email: str, to: str, email: MIMEBase):
        pass


class EmailClient:
    def __init__(self, sender: EmailSender):
        self._sender = sender

    def set_sender(self, sender: EmailSender):
        self._sender = sender

    def send_email(
        self, from_email: str, to: str, subject: str, body: str, mime_type: str = "text"
    ):
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, mime_type))
        self._sender.send(from_email, to, msg)
