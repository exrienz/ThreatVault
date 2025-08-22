from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.application.middlewares.user_context import get_current_user_id
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
        self.user_id = get_current_user_id()

    # Deprecated
    async def get_project_extended(
        self, project_id: UUID | None = None
    ) -> Sequence[Project]:
        if project_id is None:
            return await self.projectRepository.get_all()
        data = await self.projectRepository.get_one_by_id(project_id)
        return [data]

    async def create_project(self, data: dict) -> Project:
        data = {
            **data,
            "creator_id": self.user_id,
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
        await self.productRepository.delete_by_project_id(item_id)
        await self.projectRepository.delete(item_id)
        return await self.projectRepository.get_all()

    async def get_project_by_id(self, project_id: UUID) -> Project | None:
        return await self.projectRepository.get_by_id(project_id)

    async def get_one_by_id(self, project_id: UUID) -> Project:
        return await self.projectRepository.get_one_by_id(project_id)

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

    async def create_product_both_env(self, project_id: UUID, name: str):
        envs = await self.envRepository.get_all_by_filter_sequence(
            {"project_id": project_id}
        )
        if not envs:
            raise
        data = []
        for env in envs:
            data.append({"name": name, "environment_id": env.id})
        await self.productRepository.create_bulk(data)

    async def delete_product(self, product_id: UUID):
        await self.fnRevertRepository.delete_by_product_id(product_id)
        await self.productRepository.delete(product_id)

    async def get_all(self) -> Sequence[Project]:
        return await self.projectRepository.get_all()

    async def get_all_with_logs(self, env: str):
        return await self.LogRepository.get_project_list(env=env)

    async def get_all_by_filters(self, filters: dict) -> Sequence[Project]:
        return await self.projectRepository.get_all_by_filter_sequence(filters)

    async def min_year(self) -> int | None:
        return await self.projectRepository.min_year()
