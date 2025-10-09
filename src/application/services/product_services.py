import secrets
from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.domain.entity import Product
from src.domain.entity.user_access import User
from src.persistence import (
    EnvRepository,
    ProductEscalationRepository,
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
        escalationRepository: ProductEscalationRepository = Depends(),
    ):
        self.projectRepository = projectRepository
        self.productRepository = productRepository
        self.userRepository = userRepository
        self.envRepository = envRepository
        self.roleRepository = roleRepository
        self.escalationRepository = escalationRepository

    async def get_by_id(self, product_id: UUID) -> Product | None:
        return await self.productRepository.get_by_id(product_id)

    async def get_by_env_id(self, env_id: UUID) -> Sequence[Product]:
        return await self.productRepository.get_all_by_filter_sequence(
            {"environment_id": env_id}
        )

    async def get_one_by_filter(self, filters: dict) -> Product | None:
        return await self.productRepository.get_by_filter(filters)

    async def get_all_by_filter(self, filters: dict) -> Sequence[Product]:
        return await self.productRepository.get_all_by_filter_sequence(filters)

    async def get_all_by_ids(self, product_ids: list[UUID]) -> Sequence[Product]:
        return await self.productRepository.get_all_by_filter_sequence(
            {"id": product_ids}
        )

    async def manage_product_access(
        self, product_id: UUID, user_id: UUID, granted: bool = True
    ):
        access = await self.productRepository.manage_product_access(
            product_id, user_id, granted
        )
        product = await self.productRepository.get_by_id(product_id)
        user = await self.userRepository.get_by_id(user_id)
        return access, product, user

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

    async def get_users_accessable_to_product(self, product_id: UUID):
        return await self.userRepository.get_users_allowed_to_access_product(product_id)

    async def generate_api_key(self, product_id: UUID) -> Product:
        data = {
            "apiKey": secrets.token_hex(16),
        }

        res = await self.productRepository.update(product_id, data)
        if res is None:
            raise
        return res

    async def get_hosts(self, product_id: UUID) -> Sequence[str]:
        return await self.productRepository.get_hosts(product_id)

    async def get_owners_by_product_id(self, product_id) -> Sequence[User]:
        return await self.productRepository.get_owners_by_product_id(product_id)

    async def update_escalation(
        self,
        product_id: UUID,
        user_ids: list[UUID] | None = None,
        monthly: bool = False,
        weekly: bool = False,
    ):
        await self.productRepository.update(
            product_id, {"weEscalation": weekly, "moEscalation": monthly}
        )
        await self.escalationRepository.delete_update(product_id, user_ids or [])

    async def get_escalation_list(self, product_id: UUID) -> Sequence[User]:
        return await self.escalationRepository.get_escalated_user(product_id)

    async def get_escalation_options(
        self, product_id: UUID
    ) -> tuple[set[User], set[User]]:
        escalated = await self.get_escalation_list(product_id)
        allowed_user = await self.get_users_accessable_to_product(product_id)
        set_escalated = set(escalated)
        set_allowed = set(allowed_user)
        diff = set_allowed - set_escalated
        return set_escalated, diff
