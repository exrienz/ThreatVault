from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.application.dependencies import AuthServiceDep, GlobalServiceDep
from src.application.schemas.auth import UserLoginSchema, UserRegisterSchema

from ..utils import templates

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/register")
async def register_page(request: Request, globalsetting: GlobalServiceDep):
    db_setting = await globalsetting.get()
    if db_setting is None or not db_setting.login_via_email:
        raise
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
        raise
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
            "HX-Redirect": "/",
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
