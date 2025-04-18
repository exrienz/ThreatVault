from fastapi import Request

from src.application.exception.error import UnauthorizedError
from src.application.middlewares.user_context import get_current_user_id


async def verify_auth(request: Request):
    user_id = get_current_user_id()
    if user_id is None:
        raise UnauthorizedError()
