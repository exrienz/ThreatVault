from logging import Logger
from pathlib import Path

from sqlalchemy import select

from src.domain.entity import Plugin
from src.infrastructure.database import SyncSessionFactory

p = Path("./public/plugins/builtin")


def upload_builtin_plugin(logger: Logger):
    with SyncSessionFactory() as session:
        lst = list(p.glob("**/*.py"))
        file_set = {
            f"{ls.parent.name[-2:].upper()}/{ls.name.split('.')[0]}" for ls in lst
        }
        stmt = select(Plugin).where(Plugin.type == "builtin")
        db_plugins = session.execute(stmt).scalars().all()
        db_plugins_lst = {f"{str(p.env).lower()}/{p.name}" for p in db_plugins}
        need_to_update = file_set.difference(db_plugins_lst)
        if len(need_to_update) == 0:
            logger.info("All Plugins Updated")
            return

        plugins = []
        for plugin in need_to_update:
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

        logger.info(f"Added {len(plugins)} builtin plugins")
