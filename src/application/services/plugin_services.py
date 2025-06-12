from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends
from fastapi.datastructures import UploadFile

from src.application.exception.error import InvalidFile
from src.domain.entity import Plugin
from src.persistence.plugin import PluginRepository


class PluginService:
    def __init__(self, repository: PluginRepository = Depends()):
        self.repository = repository

    async def get_all(self) -> Sequence[Plugin]:
        return await self.repository.get_all()

    async def get_by_id(self, item_id: UUID) -> Plugin:
        return await self.repository.get_one_by_id(item_id)

    async def get_all_activated(self) -> Sequence[Plugin]:
        return await self.repository.get_all_by_filter({"is_active": True})

    async def create(self, data: dict, file: UploadFile):
        if file.filename is None:
            raise
        data["name"] = file.filename.split(".")[0]
        data["type"] = "custom"
        await self.upload_plugin(data, file)
        return await self.repository.create(data)

    async def update(self, item_id: UUID, data: dict, file: UploadFile | None = None):
        plugin = await self.repository.update(item_id, data)
        if file:
            await self.upload_plugin(plugin.__dict__, file)

    async def upload_plugin(self, data: dict, file: UploadFile):
        if file.content_type != "text/x-python":
            raise InvalidFile("Python")
        filepath = f"public/plugins/{data.get('type')}/{data.get('name')}.py"
        with open(filepath, "wb") as f:
            file_data = await file.read()
            f.write(file_data)
