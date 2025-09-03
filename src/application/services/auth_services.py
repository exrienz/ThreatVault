import hashlib
import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import Depends

from src.application.exception.error import (
    InactiveUser,
    InvalidAuthentication,
    SchemaException,
)
from src.config import settings
from src.domain.entity import User
from src.infrastructure.services.email.send import EmailClient
from src.infrastructure.services.email.smtp import SMTPSender
from src.persistence import AuthRepository
from src.persistence.config import GlobalRepository
from src.persistence.password_reset import PasswordResetRepository

from ..schemas.auth import TokenDataSchema, UserLoginSchema, UserRegisterSchema

# TODO: change to strategy pattern
from ..security.oauth2.password import pwd_context


class AuthService:
    def __init__(
        self,
        repository: AuthRepository = Depends(),
        global_repository: GlobalRepository = Depends(),
        reset_pass_repository: PasswordResetRepository = Depends(),
    ) -> None:
        self.repository = repository
        self.global_repository = global_repository
        self.reset_password_repository = reset_pass_repository

    async def register(self, data: UserRegisterSchema) -> User:
        user = await self.repository.get_by_filter({"username": data.username})
        if user:
            raise SchemaException("User already exists")
        data_dict = data.model_dump(exclude={"password_confirm"})
        data_dict["password"] = self.hash_password(data.password)
        return await self.repository.register(data_dict)

    async def authenticate(self, data: UserLoginSchema) -> str:
        user = await self.repository.get_by_filter({"username": data.username})
        if not user:
            raise InvalidAuthentication
        if user.password is None or not self.verify_password(
            data.password, user.password
        ):
            raise InvalidAuthentication
        if not user.active:
            raise InactiveUser
        high_priviledge = False
        if user.role.name in ("ITSE"):
            high_priviledge = True
        token_data = TokenDataSchema(
            userid=str(user.id),
            role=user.role.name,
            is_admin=user.role.super_admin,
            high_privilege=high_priviledge,
            role_id=str(user.role.id),
            required_project_access=user.role.required_project_access,
            username=user.username,
        )
        return self.create_access_token(token_data)

    def verify_password(self, input_password: str, hashed_password: str):
        return pwd_context.verify(input_password, hashed_password)

    def hash_password(self, password):
        return pwd_context.hash(password)

    def create_access_token(self, data: TokenDataSchema) -> str:
        to_encode = data.model_dump()
        expired_at = datetime.now() + timedelta(minutes=settings.JWT_EXPIRED_MINUTES)
        to_encode.update({"exp": expired_at})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    async def send_reset_password_email(self, email: str, html: str):
        user = await self.repository.get_by_filter({"email": email})
        if not user:
            return

        config = await self.global_repository.get()
        if config is None:
            raise
        smtp_client = SMTPSender(
            config.smtp_server,
            config.smtp_port,
            config.smtp_username,
            config.smtp_password,
        )

        # TODO: support other email solution
        email_provider = EmailClient(smtp_client)
        email_provider.send_email(
            "sentinel@code-x.my",  # TODO
            email,
            subject="Sentinel: Reset Password",
            body=html,
            mime_type="html",
        )

    async def get_by_filter(self, filters: dict):
        return await self.repository.get_by_filter(filters)

    async def generate_password_reset_token(self, email: str):
        user = await self.repository.get_by_filter({"email": email})
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if user is None:
            return None
        usr = {"username": user.username, "email": user.email, "token": token}
        expires = datetime.now() + timedelta(days=1)
        data = {"user_id": user.id, "expires_at": expires, "token_hash": token_hash}
        await self.reset_password_repository.invalidate_token(user.id)
        await self.reset_password_repository.create(data)
        return usr

    async def get_password_reset_user(self, token: str):
        return await self.reset_password_repository.get_user_by_token(token)

    async def reset_password(self, token: str, password: str) -> User | None:
        user_info = await self.get_password_reset_user(token)
        if user_info is None:
            raise SchemaException("Token no longer valid!")
        password_hash = self.hash_password(password)
        await self.reset_password_repository.delete(user_info.id)
        return await self.repository.update(
            user_info.user_id, {"password": password_hash}
        )
