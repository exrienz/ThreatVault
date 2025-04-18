from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Comment
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(Comment, session)

    def _options(self, stmt: Select):
        return stmt.options(selectinload(Comment.commentor))

    # TODO: Generalize this
    async def get_by_finding_name_id(self, finding_name_id: UUID) -> Sequence[Comment]:
        stmt = select(Comment).where(Comment.findingName_id == finding_name_id)
        stmt = stmt.options(selectinload(Comment.commentor))
        stmt = stmt.order_by(Comment.created_at)
        query = await self.session.execute(stmt)
        return query.scalars().all()
