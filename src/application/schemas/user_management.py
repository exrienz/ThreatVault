from uuid import UUID

from pydantic import BaseModel


class UserSearchSchema(BaseModel):
    pass


class UserUpdateSchema(BaseModel):
    # username: str
    # email: str
    active: bool
    role_id: UUID
