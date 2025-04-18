from pydantic import BaseModel


class UserRegisterSchema(BaseModel):
    email: str
    username: str
    password: str
    password_confirm: str


class UserLoginSchema(BaseModel):
    username: str
    password: str


class TokenDataSchema(BaseModel):
    userid: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class AuthTokenSchema(BaseModel):
    Authorization: str | None = None
