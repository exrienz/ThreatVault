from contextvars import ContextVar
from uuid import UUID

import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import settings

current_user_id_var: ContextVar[UUID | None] = ContextVar("current_user_id")


def get_current_user_id() -> UUID | None:
    return current_user_id_var.get(None)


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        auth = request.cookies.get("Authorization")
        # TODO: For API
        # token = request.headers.get("X-Token")
        user_info = None

        # TODO: Split function
        if auth:
            auth = auth.split(" ")
            if auth[0] == "Bearer":
                user_info = jwt.decode(
                    auth[1],
                    settings.JWT_SECRET,
                    algorithms=[
                        settings.JWT_ALGORITHM,
                    ],
                )
                current_user_id_var.set(user_info.get("userid"))
        return await call_next(request)
