from collections.abc import Sequence
from uuid import UUID, uuid4

from fastapi import Depends

from src.domain.entity import Product, Project
from src.persistence import (
    EnvRepository,
    ProductRepository,
    ProjectRepository,
    UserRepository,
)


class ProjectManagementService:
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

    async def get_project_extended(
        self, project_id: UUID | None = None
    ) -> Sequence[Project]:
        return await self.projectRepository.get_all_extend(project_id)

    async def create_project(self, data: dict) -> Project:
        # TODO: Creator ID
        creator_id = uuid4()
        data = {
            **data,
            "creator_id": creator_id,
        }
        project = await self.projectRepository.create_with_env(data)
        project_extended = await self.projectRepository.get_by_id_extend(project.id)
        if project_extended is None:
            raise
        return project_extended

    async def delete_project(self, item_id: UUID):
        project = self.projectRepository.get(item_id)
        if project is None:
            raise
        await self.projectRepository.delete(item_id)
        return await self.projectRepository.get_all()

    async def get_product_by_project_id(
        self, project_id: UUID | None = None, environment_id: UUID | None = None
    ) -> Sequence[Product]:
        return await self.productRepository.get_by_id_filter(project_id, environment_id)

    async def create_product(
        self, project_id: UUID, env_name: str, name: str
    ) -> Product:
        envs = await self.envRepository.get_by_filter(env_name, project_id)
        if envs is None:
            raise
        data = {"name": name, "environment_id": envs.id}
        return await self.productRepository.create(data)

    async def delete_product(self, product_id: UUID):
        await self.productRepository.delete(product_id)
