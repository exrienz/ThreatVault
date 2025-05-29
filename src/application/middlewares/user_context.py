from contextvars import ContextVar
from uuid import UUID

import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import settings

current_user_id_var: ContextVar[UUID | None] = ContextVar("current_user_id")
current_user_var: ContextVar[dict] = ContextVar("current_user")

current_user_perm: ContextVar[set[str]] = ContextVar("current_user_permissions")


def get_current_user_id() -> UUID | None:
    return current_user_id_var.get(None)


def get_current_user() -> dict:
    return current_user_var.get({})


def is_admin() -> bool:
    userinfo = current_user_var.get({})
    if userinfo.get("role") == "Admin":
        return True
    return False


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
                current_user_var.set(user_info)
        return await call_next(request)
