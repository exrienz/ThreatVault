from pathlib import Path

from sqlalchemy import select

from src.domain.entity import Plugin
from src.infrastructure.database import SyncSessionFactory

p = Path("./public/plugins/builtin")


def upload_builtin_plugin():
    with SyncSessionFactory() as session:
        lst = list(p.glob("**/*.py"))
        plugins = []

        stmt = select(Plugin.name)
        db_plugins = session.execute(stmt).scalars().all()
        for ls in lst:
            name = ls.name.split(".")[0]
            if name in db_plugins:
                continue
            plugin = Plugin(
                name=name, type="builtin", is_active=True, verified=True, env="VA"
            )
            plugins.append(plugin)
        session.add_all(plugins)
        session.commit()

        print(f"Added {len(plugins)} builtin plugins")
