from pathlib import Path
from sqlalchemy.orm import Session

from src.domain.entity.finding import Plugin


p = Path("./plugins/builtin")


def create_plugins(session: Session):
    lst = list(p.glob("**/*.py"))
    file_set = {f"{ls.parent.name[-2:].upper()}/{ls.name.split('.')[0]}" for ls in lst}

    plugins = []
    for plugin in file_set:
        env, name = plugin.split("/")
        plugin = Plugin(
            name=name,
            type="builtin",
            is_active=True,
            verified=True,
            env=env,
        )
        plugins.append(plugin)
    session.add_all(plugins)
    session.commit()
