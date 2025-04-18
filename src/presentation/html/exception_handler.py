from fastapi import Request

from src.application.exception.error import UnauthorizedError

from .utils import templates


async def unauthorize(request: Request, exc: UnauthorizedError):
    return templates.TemplateResponse(
        request,
        "error/401.html",
    )


exception_handlers = {UnauthorizedError: unauthorize}
