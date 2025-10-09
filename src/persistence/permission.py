from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.user_access import Permission
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(Permission, session)
