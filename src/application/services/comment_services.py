from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.application.middlewares.user_context import get_current_user_id
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
        return await self.repository.get_by_finding_name_id(fn_id)

    async def create(self, item_id: UUID, comment: str) -> Comment:
        data = {
            "comment": comment,
            "commentor_id": self.user_id,
            "findingName_id": item_id,
        }
        created_comment = await self.repository.create(data)
        return await self.repository.get_one_by_id(created_comment.id)
