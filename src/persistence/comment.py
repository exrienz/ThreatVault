from typing import Annotated

from fastapi import Depends
from sqlalchemy import Select
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
