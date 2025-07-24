from typing import Annotated

from fastapi import Depends

from ..services import (
    AuthService,
    CommentService,
    CVEService,
    EnvService,
    FindingService,
    GlobalService,
    LogService,
    ManagementViewService,
    PluginService,
    ProductService,
    ProjectManagementService,
    RemarkService,
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
MVServiceDep = Annotated[ManagementViewService, Depends()]
CVEServiceDep = Annotated[CVEService, Depends()]
RemarkServiceDep = Annotated[RemarkService, Depends()]

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
    "MVServiceDep",
    "CVEServiceDep",
    "RemarkServiceDep",
]
