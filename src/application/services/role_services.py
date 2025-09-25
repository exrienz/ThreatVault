from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.application.exception.error import SchemaException
from src.domain.entity import Role
from src.domain.entity.user_access import Permission
from src.persistence import RoleRepository
from src.persistence.permission import PermissionRepository


class RoleService:
    def __init__(
        self,
        repository: RoleRepository = Depends(),
        permission_repository: PermissionRepository = Depends(),
    ):
        self.repository = repository
        self.permission_repository = permission_repository

    def _cannot_update_list(self) -> list[str]:
        return self.repository._cannot_update_list()

    async def get_all(self) -> Sequence[Role]:
        return await self.repository.get_all()

    async def get_all_with_permissions(self):
        return await self.repository.get_roles_with_permissions()

    async def get_one_with_permissions(self, filters: dict):
        return await self.repository.get_with_permissions_by_filters(filters)

    async def update_role(self, role_id: UUID, data: dict):
        return await self.repository.update(role_id, data)

    async def update_permissions(self, role_id: UUID, permissions: list[UUID]):
        return await self.repository.update_permissions(role_id, permissions)

    async def get_all_permissions(self) -> Sequence[Permission]:
        return await self.permission_repository.get_all()

    async def can_update(self, role_id: UUID):
        res = await self.repository._can_update(role_id)
        if not res:
            raise SchemaException("This role cannot be update")
