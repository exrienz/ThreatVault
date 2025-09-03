from typing import Annotated

import jwt
from fastapi import Depends

from src.config import settings
from src.persistence import UserRepository

from ..security.oauth2.password import oauth2_password_scheme

# TODO: change to strategy pattern


class PermissionService:
    def __init__(self, user_repository: UserRepository = Depends()) -> None:
        self.user_repository = user_repository

    async def get_current_user(
        self, token: Annotated[str, Depends(oauth2_password_scheme)]
    ):
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=settings.JWT_ALGORITHM
            )
            username = payload.get("sub")
            if username is None:
                raise
        except jwt.InvalidTokenError:
            raise
        user = await self.user_repository.get_by_filter({"username": username})
        if user is None:
            raise
        if not user.active:
            raise
        return user
