from sqlalchemy import func, select
from sqlalchemy_utils import create_database, database_exists

from src.config import default_roles
from src.domain.entity import Base, GlobalConfig, Role
from src.infrastructure.database import SyncSessionFactory, sync_db_conn, sync_engine


def startup_db():
    print("Creating DB")
    if not database_exists(sync_db_conn):
        create_database(sync_db_conn)
    Base.metadata.create_all(bind=sync_engine)

    print("DB Created")

    create_default_roles()
    default_global_setting()


def create_default_roles():
    print("Creating Default Role")
    with SyncSessionFactory() as session:
        stmt = select(func.count(Role.id))
        roles = session.execute(stmt).scalar_one()
        if roles == 0:
            role_list = [Role(**data) for data in default_roles]
            session.add_all(role_list)
            session.commit()
    print("Default Role Created")


def default_global_setting():
    with SyncSessionFactory() as session:
        stmt = select(func.count(GlobalConfig.id))
        config = session.execute(stmt).scalar_one()
        if config == 0:
            session.add(GlobalConfig())
            session.commit()
