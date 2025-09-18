from uuid import UUID

from fastapi import Depends
from sqlalchemy import ARRAY, String, case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import Role
from src.domain.entity.user_access import Permission, RolePermission
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(Role, session)

    async def get_by_name(self, role_name: str) -> Role | None:
        stmt = select(Role).where(Role.name == role_name)
        query = await self.session.execute(stmt)
        return query.scalar()

    async def get_with_permissions_by_filters(self, filters: dict):
        stmt = (
            select(
                Role.id,
                Role.name,
                Role.super_admin,
                Role.required_project_access,
                func.coalesce(
                    func.array_agg(
                        func.distinct(Permission.scope), type_=ARRAY(String)
                    ),
                    [],
                ).label("permissions"),
            )
            .select_from(Role)
            .join(RolePermission, isouter=True)
            .join(Permission, isouter=True)
            .group_by(
                Role.id, Role.name, Role.super_admin, Role.required_project_access
            )
        )
        stmt = self._advanced_filtering(stmt, filters)
        query = await self.session.execute(stmt)
        return query.first()

    async def get_roles_with_permissions(self):
        stmt = (
            select(
                Role.id,
                Role.name,
                Role.super_admin,
                Role.required_project_access,
                func.coalesce(
                    func.array_agg(
                        case((Permission.scope.isnot(None), Permission.scope)),
                        type_=ARRAY(String),
                    ),
                    [],
                ).label("permissions"),
            )
            .select_from(Role)
            .join(RolePermission, isouter=True)
            .join(Permission, isouter=True)
            .group_by(
                Role.id, Role.name, Role.super_admin, Role.required_project_access
            )
            .order_by(Role.name)
        )
        query = await self.session.execute(stmt)
        return query.all()

    async def update_permissions(self, role_id: UUID, permissions: list[UUID]):
        delete_stmt = delete(RolePermission).where(RolePermission.role_id == role_id)
        await self.session.execute(delete_stmt)

        lst = [
            RolePermission(role_id=role_id, permission_id=permission)
            for permission in permissions
        ]

        self.session.add_all(lst)
        await self.session.commit()

    async def _can_update(self, role_id: UUID) -> bool:
        stmt = select(Role).where(
            Role.id == role_id, Role.name.not_in(self._cannot_update_list())
        )
        query = await self.session.execute(stmt)
        role = query.scalars().first()
        return role is not None

    def _cannot_update_list(self) -> list[str]:
        return ["Admin", "ITSE", "Service"]
