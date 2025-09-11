from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.entity import Environment
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository
from src.presentation.dependencies import get_allowed_project_ids


class EnvRepository(BaseRepository[Environment]):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        project_ids: Annotated[list[UUID] | None, Depends(get_allowed_project_ids)],
    ):
        super().__init__(Environment, session, project_ids)

    def _options(self, stmt: Select) -> Select:
        return stmt.options(joinedload(Environment.project)).options(
            joinedload(Environment.products)
        )

    def _project_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_project_ids is None:
            return stmt
        return stmt.where(Environment.project_id.in_(self.allowed_project_ids))
