from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Comment
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository
from src.presentation.dependencies import get_allowed_product_ids


class CommentRepository(BaseRepository[Comment]):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        product_ids: Annotated[list[UUID] | None, Depends(get_allowed_product_ids)],
    ):
        super().__init__(Comment, session, product_ids)

    def _options(self, stmt: Select):
        return stmt.options(selectinload(Comment.commentor))

    def _product_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_product_ids is None:
            return stmt
        return stmt.where(Comment.product_id.in_(self.allowed_product_ids))
