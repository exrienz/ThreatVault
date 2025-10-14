import os
import re
from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends
from fastapi.datastructures import UploadFile

from src.application.exception.error import InvalidFile, SchemaException
from src.domain.entity import Plugin
from src.persistence.plugin import PluginRepository


class PluginService:
    def __init__(self, repository: PluginRepository = Depends()):
        self.repository = repository

    async def get_all(self) -> Sequence[Plugin]:
        return await self.repository.get_all()

    async def get_by_id(self, item_id: UUID) -> Plugin:
        return await self.repository.get_one_by_id(item_id)

    async def get_by_filter(self, filters: dict) -> Plugin | None:
        return await self.repository.get_by_filter(filters)

    async def get_all_activated(self, filters: dict | None = None) -> Sequence[Plugin]:
        filters = filters if filters else {}
        return await self.repository.get_all_by_filter_sequence(
            {"is_active": True, **filters}
        )

    async def create(self, data: dict, file: UploadFile):
        if file.filename is None:
            raise
        data["name"] = file.filename.split(".")[0]
        data["type"] = "custom"
        plugin = await self.get_by_filter(
            {
                "name": data.get("name"),
                "type": "custom",
                "env": data.get("env", "VA").upper(),
            }
        )
        if plugin:
            raise InvalidFile(
                f"Filename: {data.get('name')} with type {data.get('env')} already exists"  # noqa: E501
            )
        await self.upload_plugin(data, file)
        return await self.repository.create(data)

    async def update(self, item_id: UUID, data: dict, file: UploadFile | None = None):
        plugin = await self.repository.update(item_id, data)
        if file:
            await self.upload_plugin(plugin.__dict__, file)
        return plugin

    async def upload_plugin(self, data: dict, file: UploadFile):
        if file.filename is None:
            raise InvalidFile("Missing Filename")
        if not file.filename.endswith(".py"):
            raise InvalidFile("Required .py")
        filepath = f"./plugins/{data.get('type', '').lower()}/"
        filepath += f"{data.get('env', 'VA').lower()}/{data.get('name')}.py"
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", data.get("name", "")):
            raise ValueError(
                "Invalid plugin name — only letters, digits, _ and - allowed"
            )
        with open(filepath, "wb") as f:
            file_data = await file.read()
            f.write(file_data)

    async def delete(self, item_id: UUID):
        data = await self.repository.get_by_id(item_id)
        if data is None:
            return
        if data.type == "builtin":
            raise SchemaException("Cannot delete builtin plugin!")
        env = data.env or "va"
        filepath = f"./plugins/{data.type.lower()}"
        filepath += f"/{env.lower()}/{data.name}.py"
        if os.path.exists(filepath):
            os.remove(filepath)
        await self.repository.delete(item_id)
