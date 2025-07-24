from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.domain.entity.finding import AdditionalRemark
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository


class AdditionalRemarkRepository(BaseRepository[AdditionalRemark]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(AdditionalRemark, session)
