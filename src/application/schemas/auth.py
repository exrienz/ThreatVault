from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, model_validator
from typing_extensions import Self

from src.application.exception.error import SchemaException


class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str
    password: str
    password_confirm: str

    @model_validator(mode="after")
    def password_validation(self) -> Self:
        if len(self.password) < 8:
            raise SchemaException("Password must have at least 8 characters")
        if self.password != self.password_confirm:
            raise SchemaException("Passwords do not match")
        return self


class UserLoginSchema(BaseModel):
    username: str
    password: str


class TokenDataSchema(BaseModel):
    userid: str
    role: str
    role_id: str
    is_admin: bool
    high_privilege: bool
    required_project_access: bool
    username: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class AuthTokenSchema(BaseModel):
    Authorization: str | None = None


class UserResetPasswordSchema(BaseModel):
    current_pass: str
    new_pass: str
    confirm_pass: str

    @model_validator(mode="after")
    def password_validation(self) -> Self:
        if len(self.new_pass) < 8:
            raise HTTPException(422, "Password must have at least 8 characters")
        if self.new_pass != self.confirm_pass:
            raise HTTPException(422, "Passwords do not match")
        return self
