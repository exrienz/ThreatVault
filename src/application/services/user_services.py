from collections.abc import Sequence
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException
from pydantic import PositiveInt

from src.application.exception.error import SchemaException
from src.application.middlewares.user_context import get_current_user_id
from src.domain.entity import Product, User
from src.persistence import ProjectRepository, UserRepository

from ..schemas.auth import AuthTokenSchema, UserResetPasswordSchema
from ..security.oauth2.password import pwd_context


class UserService:
    def __init__(
        self,
        repository: UserRepository = Depends(),
        projectRepository: ProjectRepository = Depends(),
        auth: AuthTokenSchema = Cookie(),
    ):
        self.repository = repository
        self.projectRepository = projectRepository
        self.auth = auth

    async def get_all(
        self,
        page: PositiveInt = 1,
        filters: dict | None = None,
        pagination: bool = True,
    ):
        return await self.repository.get_all_pagination(page, filters, pagination)

    async def get_by_id(self, user_id: UUID) -> User:
        return await self.repository.get_one_by_id(user_id)

    async def get_me(self) -> User:
        user_id = get_current_user_id()
        if user_id is None:
            raise
        return await self.repository.get_one_by_id(user_id)

    async def get_by_emails(self, emails: list[str]) -> Sequence[User]:
        return await self.repository.get_all_by_filter_sequence(
            {User.email.in_: emails}
        )

    # create schema
    async def create(self, data: dict) -> User:
        user = await self.repository.get_by_filter({"email": data.get("email")})
        if user:
            raise SchemaException(f"User with {data.get('email')} already exists!")
        return await self.repository.create(data)

    async def create_bulk(self, data: list[dict]):
        return await self.repository.create_bulk(data)

    async def update(self, user_id: UUID, data: dict):
        return await self.repository.update(user_id, data)

    async def delete(self, user_id: UUID):
        return await self.repository.delete(user_id)

    async def delete_me(self):
        user_id = get_current_user_id()
        if user_id is None:
            return
        return await self.repository.delete(user_id)

    async def get_accessible_project(self, user_id: UUID):
        products = await self.repository.get_accessible_product(user_id)
        res: dict[str, list[Product]] = {}
        for product in products:
            res_id = product.environment.project.name
            if (data := res.get(res_id)) is not None:
                data.append(product)
            else:
                res[res_id] = [product]
        return res

    async def reset_password(self, data: UserResetPasswordSchema):
        if data.current_pass == data.new_pass:
            raise HTTPException(422, "Current and New Password must be different")
        user_id = get_current_user_id()
        if user_id is None:
            raise
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise
        if user is None and user.password != data.current_pass:
            raise HTTPException(422, "Wrong Password")
        password = pwd_context.hash(data.new_pass)
        return await self.repository.update(user_id, {"password": password})
