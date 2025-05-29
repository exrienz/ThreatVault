from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.application.exception.error import (
    InactiveUser,
    InvalidAuthentication,
    SchemaException,
    UnauthorizedError,
)

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


async def inactiveUser(request: Request, exc: InactiveUser):
    return templates.TemplateResponse(
        request,
        "error/alert.html",
        {"msg": "Contact Admin to activate your account!"},
        status_code=401,
        headers={
            "HX-Retarget": "#error-alert-id",
        },
    )


async def httpException(request: Request, exc: HTTPException):
    if exc.status_code in [401, 404, 500]:
        return templates.TemplateResponse(
            request,
            f"error/{exc.status_code}.html",
            {"msg": exc.detail},
            status_code=exc.status_code,
        )
    return JSONResponse(content=str(exc.detail), status_code=exc.status_code)


async def schema_invalid_handler(request: Request, exc: SchemaException):
    return templates.TemplateResponse(
        request,
        "error/alert.html",
        {"msg": exc},
        status_code=422,
        headers={
            "HX-Retarget": "#error-alert-id",
        },
    )


exception_handlers = {
    UnauthorizedError: unauthorize,
    InvalidAuthentication: invalidAuthentication,
    InactiveUser: inactiveUser,
    HTTPException: httpException,
    SchemaException: schema_invalid_handler,
    StarletteHTTPException: httpException,
}
