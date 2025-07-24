from fastapi import Depends

from src.persistence import (
    EnvRepository,
    FindingRevertRepository,
    LogRepository,
    ProductRepository,
    ProjectRepository,
    UserRepository,
)


class ManagementViewService:
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
