from uuid import UUID

from pydantic import BaseModel


class UserSearchSchema(BaseModel):
    email: str | None = None
    role: str | None = None
    active: bool | None = None


class UserUpdateSchema(BaseModel):
    # username: str
    # email: str
    active: bool
    role_id: UUID
