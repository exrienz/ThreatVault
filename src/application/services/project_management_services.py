from collections.abc import Sequence
from uuid import UUID, uuid4

from fastapi import Depends

from src.domain.entity import Product, Project
from src.persistence import (
    EnvRepository,
    FindingRevertRepository,
    LogRepository,
    ProductRepository,
    ProjectRepository,
    UserRepository,
)


# TODO: Re-organized and re-structure
class ProjectManagementService:
    def __init__(
        self,
        projectRepository: ProjectRepository = Depends(),
        productRepository: ProductRepository = Depends(),
        userRepository: UserRepository = Depends(),
        envRepository: EnvRepository = Depends(),
        logRepository: LogRepository = Depends(),
        fnRevertRepository: FindingRevertRepository = Depends(),
    ):
        self.projectRepository = projectRepository
        self.productRepository = productRepository
        self.userRepository = userRepository
        self.envRepository = envRepository
        self.LogRepository = logRepository
        self.fnRevertRepository = fnRevertRepository

    async def get_project_extended(
        self, project_id: UUID | None = None
    ) -> Sequence[Project]:
        if project_id is None:
            return await self.projectRepository.get_all()
        data = await self.projectRepository.get_one_by_id(project_id)
        return [data]

    async def create_project(self, data: dict) -> Project:
        # TODO: Creator ID
        creator_id = uuid4()
        data = {
            **data,
            "creator_id": creator_id,
        }
        project = await self.projectRepository.create_with_env(data)
        project_extended = await self.projectRepository.get_by_id(project.id)
        if project_extended is None:
            raise
        return project_extended

    async def delete_project(self, item_id: UUID):
        project = await self.projectRepository.get(item_id)
        if project is None:
            raise
        await self.fnRevertRepository.delete_by_project_id(project.id)
        await self.projectRepository.delete(item_id)
        return await self.projectRepository.get_all()

    async def get_project_by_id(self, project_id: UUID) -> Project | None:
        return await self.projectRepository.get_by_id(project_id)

    # TODO: change the function name
    async def get_product_by_project_id(
        self, project_id: UUID | None = None, environment_id: UUID | None = None
    ) -> Sequence[Product]:
        return await self.productRepository.get_by_id_filter(project_id, environment_id)

    async def create_product(
        self, project_id: UUID, env_name: str, name: str
    ) -> Product:
        envs = await self.envRepository.get_by_filter(
            {"name": env_name, "project_id": project_id}
        )
        if envs is None:
            raise
        data = {"name": name, "environment_id": envs.id}
        return await self.productRepository.create(data)

    async def delete_product(self, product_id: UUID):
        await self.fnRevertRepository.delete_by_product_id(product_id)
        await self.productRepository.delete(product_id)

    async def get_all(self) -> Sequence[Project]:
        return await self.projectRepository.get_all()

    async def get_all_with_logs(self):
        return await self.LogRepository.get_project_list()
