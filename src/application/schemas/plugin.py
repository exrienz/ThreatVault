from typing import Optional

from pydantic import BaseModel


class PluginCreateSchema(BaseModel):
    name: Optional[str]
    description: Optional[str]
    config: Optional[str]
