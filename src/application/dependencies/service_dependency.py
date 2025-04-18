from typing import Annotated

from fastapi import Depends

from ..services import (
    AuthService,
    CommentService,
    EnvService,
    FindingService,
    GlobalService,
    LogService,
    PluginService,
    ProductService,
    ProjectManagementService,
    RoleService,
    TokenService,
    UserService,
)

ProductServiceDep = Annotated[ProductService, Depends()]
LogServiceDep = Annotated[LogService, Depends()]
FindingServiceDep = Annotated[FindingService, Depends()]
GlobalServiceDep = Annotated[GlobalService, Depends()]
PluginServiceDep = Annotated[PluginService, Depends()]
UserServiceDep = Annotated[UserService, Depends()]
RoleServiceDep = Annotated[RoleService, Depends()]
AuthServiceDep = Annotated[AuthService, Depends()]
CommentServiceDep = Annotated[CommentService, Depends()]
ProjectManagementServiceDep = Annotated[ProjectManagementService, Depends()]
EnvServiceDep = Annotated[EnvService, Depends()]
TokenServiceDep = Annotated[TokenService, Depends()]

__all__ = [
    "AuthServiceDep",
    "CommentServiceDep",
    "FindingServiceDep",
    "GlobalServiceDep",
    "LogServiceDep",
    "PluginServiceDep",
    "ProductServiceDep",
    "ProjectManagementServiceDep",
    "RoleServiceDep",
    "UserServiceDep",
    "EnvServiceDep",
    "TokenServiceDep",
]
