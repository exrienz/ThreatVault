from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.application.dependencies import AuthServiceDep, GlobalServiceDep
from src.application.middlewares.user_context import get_current_user_id
from src.application.schemas.auth import (
    PasswordResetSchema,
    UserLoginSchema,
    UserRegisterSchema,
)

from ..utils import templates

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/register")
async def register_page(request: Request, globalsetting: GlobalServiceDep):
    db_setting = await globalsetting.get()
    if db_setting is None or not db_setting.login_via_email:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "pages/auth/register.html")


@router.post("/register")
async def register(
    request: Request,
    service: AuthServiceDep,
    data: Annotated[UserRegisterSchema, Form()],
):
    await service.register(data)
    return templates.TemplateResponse(
        request,
        "empty.html",
        headers={"HX-Redirect": "/auth/login"},
    )


@router.get("/login")
async def login_page(request: Request, globalsetting: GlobalServiceDep):
    db_setting = await globalsetting.get()
    if db_setting is None or not db_setting.login_via_email:
        raise HTTPException(404)

    user = get_current_user_id()
    if user:
        return templates.TemplateResponse(
            request,
            "error/loggedIn.html",
        )

    return templates.TemplateResponse(request, "pages/auth/login.html")


@router.post("/login")
async def login(
    request: Request,
    service: AuthServiceDep,
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    auth_data = UserLoginSchema(username=data.username, password=data.password)
    token = await service.authenticate(auth_data)
    response = templates.TemplateResponse(
        request,
        "empty.html",
        headers={
            "HX-Redirect": "/management-view/vapt",
        },
    )
    response.set_cookie("Authorization", f"Bearer {token}")
    return response


@router.post("/logout")
async def logout(request: Request):
    response = templates.TemplateResponse(
        request,
        "empty.html",
        headers={
            "HX-Redirect": "/auth/login",
        },
    )
    response.delete_cookie("Authorization")
    return response


@router.get("/reset-password")
async def password_forgot_page(request: Request):
    response = templates.TemplateResponse(
        request,
        "pages/auth/reset_password/email_page.html",
    )
    return response


@router.post("/reset-password")
async def send_reset_password_email(
    request: Request,
    service: AuthServiceDep,
    background_tasks: BackgroundTasks,
    email: Annotated[str, Form()],
):
    async def send_email():
        user_info = await service.generate_password_reset_token(email)
        if user_info is None:
            return
        email_template = templates.TemplateResponse(
            request,
            "pages/auth/reset_password/email_template.html",
            user_info,
        )
        html = bytes(email_template.body)
        await service.send_reset_password_email(email, html.decode())

    background_tasks.add_task(send_email)
    return templates.TemplateResponse(
        request, "pages/auth/reset_password/email_response.html"
    )


@router.get("/reset-password/{token}")
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse(
        request, "pages/auth/reset_password/new_password.html"
    )


@router.post("/reset-password/{token}")
async def reset_password(
    request: Request,
    service: AuthServiceDep,
    token: str,
    data: Annotated[PasswordResetSchema, Form()],
):
    await service.reset_password(token, data.new_pass)
    return templates.TemplateResponse(request, "pages/auth/reset_password/success.html")
