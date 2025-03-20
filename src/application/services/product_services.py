from uuid import UUID

from fastapi import Depends

from src.domain.entity import Product
from src.persistence import (
    EnvRepository,
    ProductRepository,
    ProjectRepository,
    UserRepository,
)


class ProductService:
    def __init__(
        self,
        projectRepository: ProjectRepository = Depends(),
        productRepository: ProductRepository = Depends(),
        userRepository: UserRepository = Depends(),
        envRepository: EnvRepository = Depends(),
    ):
        self.projectRepository = projectRepository
        self.productRepository = productRepository
        self.userRepository = userRepository
        self.envRepository = envRepository

    async def get_by_id(self, product_id: UUID) -> Product | None:
        product = await self.productRepository.get_by_id(product_id)
        return product
