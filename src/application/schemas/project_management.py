from uuid import UUID

from pydantic import BaseModel


class ProjectCreateSchema(BaseModel):
    name: str
    type_: str


class ProjectCreateInternalSchema(ProjectCreateSchema):
    creator_id: UUID


class ProjectResponseSchema(ProjectCreateInternalSchema):
    pass


class ProjectManagementResponse(BaseModel):
    projects: list[ProjectResponseSchema]
