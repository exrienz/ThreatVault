from typing import Annotated

import jwt
from fastapi import Cookie

from src.config import settings
from src.application.middlewares.user_context import (
    current_user_id_var,
    current_user_var,
)


class SetContextUser:
    async def __call__(
        self,
        Authorization: Annotated[str | None, Cookie()] = None,
    ):
        if Authorization is None:
            return

        auth = Authorization.split(" ")
        if auth[0] == "Bearer":
            user_info = jwt.decode(
                auth[1],
                settings.JWT_SECRET,
                algorithms=[
                    settings.JWT_ALGORITHM,
                ],
            )
            current_user_id_var.set(user_info.get("userid"))
            current_user_var.set(user_info)
