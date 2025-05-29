import secrets
from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.domain.entity import Product, ProductUserAccess
from src.domain.entity.user_access import User
from src.persistence import (
    EnvRepository,
    ProductRepository,
    ProjectRepository,
    RoleRepository,
    UserRepository,
)


class ProductService:
    def __init__(
        self,
        projectRepository: ProjectRepository = Depends(),
        productRepository: ProductRepository = Depends(),
        userRepository: UserRepository = Depends(),
        envRepository: EnvRepository = Depends(),
        roleRepository: RoleRepository = Depends(),
    ):
        self.projectRepository = projectRepository
        self.productRepository = productRepository
        self.userRepository = userRepository
        self.envRepository = envRepository
        self.roleRepository = roleRepository

    async def get_by_id(self, product_id: UUID) -> Product | None:
        return await self.productRepository.get_by_id(product_id)

    async def get_by_env_id(self, env_id: UUID) -> Sequence[Product]:
        return await self.productRepository.get_all_by_filter(
            {"environment_id": env_id}
        )

    async def manage_product_access(
        self, product_id: UUID, user_id: UUID, granted: bool = True
    ) -> ProductUserAccess | None:
        return await self.productRepository.manage_product_access(
            product_id, user_id, granted
        )

    async def get_products_with_owner(self):
        role = await self.roleRepository.get_by_name("Owner")
        if role is None:
            raise

        return await self.productRepository.product_access_list(role.id)

    async def get_products_user_accessible_list(
        self,
        product_id: UUID,
        allowed: bool = True,
        exclude_roles: list | None = None,
    ):
        return await self.userRepository.get_users_with_product_accesibility(
            product_id, allowed, exclude_roles
        )

    async def generate_api_key(self, product_id: UUID) -> Product:
        data = {
            "apiKey": secrets.token_hex(16),
        }

        return await self.productRepository.update(product_id, data)

    async def get_hosts(self, product_id: UUID) -> Sequence[str]:
        return await self.productRepository.get_hosts(product_id)

    async def get_owners_by_product_id(self, product_id) -> Sequence[User]:
        return await self.productRepository.get_owners_by_product_id(product_id)
