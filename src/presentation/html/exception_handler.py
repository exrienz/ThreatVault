import openai
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from jwt import ExpiredSignatureError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.application.exception.error import (
    InactiveUser,
    InvalidAuthentication,
    InvalidFile,
    InvalidInput,
    LLMException,
    SchemaException,
    UnauthorizedError,
)

from .utils import templates


def unauthorize(request: Request, exc: UnauthorizedError):
    return templates.TemplateResponse(
        request,
        "error/401.html",
        status_code=401,
    )


def invalidAuthentication(request: Request, exc: InvalidAuthentication):
    return templates.TemplateResponse(
        request,
        "error/alert.html",
        {"msg": "Invalid Credential"},
        status_code=401,
        headers={
            "HX-Retarget": "#error-alert-id",
        },
    )


def inactiveUser(request: Request, exc: InactiveUser):
    return templates.TemplateResponse(
        request,
        "error/alert.html",
        {"msg": "Contact Admin to activate your account!"},
        status_code=401,
        headers={
            "HX-Retarget": "#error-alert-id",
        },
    )


def httpException(request: Request, exc: HTTPException):
    path = request.url.path
    if exc.status_code == 403 and path == "/":
        return RedirectResponse(str(request.base_url) + "management-view/vapt")
    if exc.status_code in [401, 403, 404, 500]:
        return templates.TemplateResponse(
            request,
            f"error/{exc.status_code}.html",
            {"msg": exc.detail},
            status_code=exc.status_code,
        )
    return JSONResponse(content=str(exc.detail), status_code=exc.status_code)


def schema_invalid_handler(request: Request, exc: SchemaException):
    return templates.TemplateResponse(
        request,
        "error/alert.html",
        {"msg": exc},
        status_code=422,
        headers={
            "HX-Retarget": "#error-alert-id",
        },
    )


def invalid_file_upload(request: Request, exc: InvalidFile):
    return templates.TemplateResponse(
        request,
        "error/toast.html",
        {"msg": exc.msg},
        status_code=422,
    )


def invalid_input(request: Request, exc: InvalidInput):
    return templates.TemplateResponse(
        request,
        "error/toast.html",
        {"msg": exc},
        status_code=422,
    )


def jwt_expired_handler(request: Request, exc: ExpiredSignatureError):
    return templates.TemplateResponse(
        request,
        "error/session_expired.html",
    )


def llm_error(request: Request, exc: openai.BadRequestError):
    return JSONResponse(exc.body.get("message"), exc.status_code)


def llm_custom_error(request: Request, exc: LLMException):
    return JSONResponse(exc.msg, 400)


exception_handlers = {
    UnauthorizedError: unauthorize,
    InvalidAuthentication: invalidAuthentication,
    InactiveUser: inactiveUser,
    HTTPException: httpException,
    SchemaException: schema_invalid_handler,
    StarletteHTTPException: httpException,
    InvalidFile: invalid_file_upload,
    InvalidInput: invalid_input,
    ExpiredSignatureError: jwt_expired_handler,
    openai.BadRequestError: llm_error,
    LLMException: llm_custom_error,
}
