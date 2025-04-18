import importlib.util
import pathlib
import sys
from collections.abc import Sequence
from types import ModuleType
from uuid import UUID

from fastapi import Depends
from fastapi.datastructures import UploadFile

from src.domain.entity import Plugin
from src.persistence.plugin import PluginRepository

# TODO: Lazy Import


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
        data["is_custom"] = True
        if file.filename is None:
            raise
        data["name"] = file.filename.split(".")[0]
        await self.upload_plugin(data, file)
        return await self.repository.create(data)

    async def update(self, item_id: UUID, data: dict, file: UploadFile | None = None):
        plugin = await self.repository.update(item_id, data)
        if file:
            await self.upload_plugin(plugin.__dict__, file)

    async def upload_plugin(self, data: dict, file: UploadFile):
        if file.content_type != "text/x-python":
            raise
        filepath = f"public/plugins/{data.get('type')}/{data.get('name')}.py"
        with open(filepath, "wb") as f:
            file_data = await file.read()
            f.write(file_data)

    @classmethod
    def plugin_import(cls, name: str, filename: str) -> ModuleType:
        ph = pathlib.Path(__file__).cwd()
        path = f"{ph}/public/plugins/{filename}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise
        loader = importlib.util.LazyLoader(spec.loader)
        spec.loader = loader
        module = importlib.util.module_from_spec(spec)
        if module is None:
            raise
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
