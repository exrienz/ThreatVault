import importlib.util
import pathlib
import sys
from types import ModuleType

# TODO: Lazy Import


class PluginService:
    @classmethod
    async def create(cls): ...

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
