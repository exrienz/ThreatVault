import hashlib
from datetime import datetime
from uuid import UUID

import pytz
from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy import delete as SQL_DELETE
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity.user_access import UserPasswordReset
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class PasswordResetRepository(BaseRepository[UserPasswordReset]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(UserPasswordReset, session)

    async def get_user_by_token(self, token: str) -> UserPasswordReset | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stmt = (
            select(UserPasswordReset)
            .where(
                UserPasswordReset.token_hash == token_hash,
                UserPasswordReset.expires_at >= datetime.now(pytz.utc),
            )
            .order_by(UserPasswordReset.expires_at.desc())
        )

        stmt = self._options(stmt)
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def invalidate_token(self, user_id: UUID):
        stmt = SQL_DELETE(UserPasswordReset).where(UserPasswordReset.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()

    def _options(self, stmt: Select) -> Select:
        return stmt.options(selectinload(UserPasswordReset.user))
