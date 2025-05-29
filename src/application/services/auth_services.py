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
from src.persistence import AuthRepository

from ..schemas.auth import TokenDataSchema, UserLoginSchema, UserRegisterSchema

# TODO: change to strategy pattern
from ..security.oauth2.password import pwd_context


class AuthService:
    def __init__(self, repository: AuthRepository = Depends()) -> None:
        self.repository = repository

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
        expired_at = datetime.now() + timedelta(settings.JWT_EXPIRED_MINUTES)
        to_encode.update({"exp": expired_at})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
