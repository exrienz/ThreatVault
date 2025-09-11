from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.domain.entity.finding import AdditionalRemark
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository
from src.presentation.dependencies import get_allowed_product_ids


class AdditionalRemarkRepository(BaseRepository[AdditionalRemark]):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        product_ids: Annotated[list[UUID] | None, Depends(get_allowed_product_ids)],
    ):
        super().__init__(AdditionalRemark, session, product_ids=product_ids)

    def _product_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_product_ids is None:
            return stmt
        return stmt.where(AdditionalRemark.product_id.in_(self.allowed_product_ids))
