from datetime import datetime, timedelta

import jwt

from src.application.schemas.auth import TokenDataSchema
from src.config import settings
from src.domain.entity.user_access import User


def generate_access_token(user: User):
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
    return create_access_token(token_data)


def create_access_token(data: TokenDataSchema) -> str:
    to_encode = data.model_dump()
    expired_at = datetime.now() + timedelta(minutes=settings.JWT_EXPIRED_MINUTES)
    to_encode.update({"exp": expired_at})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt
