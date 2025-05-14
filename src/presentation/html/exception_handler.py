from fastapi import Request

from src.application.exception.error import InvalidAuthentication, UnauthorizedError

from .utils import templates


async def unauthorize(request: Request, exc: UnauthorizedError):
    return templates.TemplateResponse(
        request,
        "error/401.html",
        status_code=401,
    )


async def invalidAuthentication(request: Request, exc: InvalidAuthentication):
    return templates.TemplateResponse(
        request,
        "error/alert.html",
        {"msg": "Invalid Credential"},
        status_code=401,
        headers={
            "HX-Retarget": "#error-alert-id",
        },
    )


exception_handlers = {
    UnauthorizedError: unauthorize,
    InvalidAuthentication: invalidAuthentication,
}
