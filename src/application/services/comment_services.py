from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.application.exception.error import UnauthorizedError
from src.application.middlewares.user_context import (
    get_current_user_id,
    is_admin,
)
from src.domain.entity.finding import Comment
from src.persistence import CommentRepository


class CommentService:
    def __init__(
        self,
        repository: CommentRepository = Depends(),
    ):
        self.repository = repository
        self.user_id = get_current_user_id()

    async def get_by_finding_name_id(self, fn_id: UUID) -> Sequence[Comment]:
        return await self.repository.get_all_by_filter_sequence(
            {"finding_name_id": fn_id}
        )

    async def get_all_by_filter(self, filters: dict) -> Sequence[Comment]:
        return await self.repository.get_all_by_filter_sequence(filters)

    async def create(
        self, item_id: UUID, comment: str, product_id: UUID | None = None
    ) -> Comment:
        data = {
            "comment": comment,
            "commentor_id": self.user_id,
            "finding_name_id": item_id,
            "product_id": product_id,
        }
        created_comment = await self.repository.create(data)
        return await self.repository.get_one_by_id(created_comment.id)

    async def delete(self, comment_id: UUID, bypass: bool = False):
        comment = await self.repository.get_one_by_id(comment_id)
        if self.user_id is None:
            raise UnauthorizedError
        if bypass or is_admin() or str(comment.commentor_id) == self.user_id:
            return await self.repository.delete(comment_id)
