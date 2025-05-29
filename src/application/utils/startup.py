from sqlalchemy import func, select
from sqlalchemy_utils import create_database, database_exists

from src.config import default_permissions, default_role_permission, default_roles
from src.domain.entity import Base, GlobalConfig, Role
from src.domain.entity.user_access import Permission, RolePermission
from src.infrastructure.database import SyncSessionFactory, sync_db_conn, sync_engine

from .plugin import upload_builtin_plugin


def startup_db():
    print("Creating DB")
    if not database_exists(sync_db_conn):
        create_database(sync_db_conn)
    Base.metadata.create_all(bind=sync_engine)

    print("DB Created")

    create_default_roles()
    default_global_setting()
    upload_builtin_plugin()
    creating_default_permission()
    create_role_permissions()


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


def creating_default_permission():
    print("Creating Default Permissions")
    with SyncSessionFactory() as session:
        stmt = select(func.count(Permission.id))
        perm = session.execute(stmt).scalar_one()
        if perm == 0:
            role_list = [Permission(**data) for data in default_permissions]
            session.add_all(role_list)
            session.commit()
    print("Default Permission Created")


def create_role_permissions():
    print("Assinging Default Permissions")
    with SyncSessionFactory() as session:
        stmt = select(func.count(RolePermission.id))
        perm = session.execute(stmt).scalar_one()
        if perm == 0:
            for data in default_role_permission:
                role_str = data.get("role")
                role_stmt = select(Role.id).where(Role.name == role_str)
                perm_stmt = select(Permission.id).where(
                    Permission.scope.in_(data.get("scopes", []))
                )
                role = session.scalar(role_stmt)
                perm_ids = session.scalars(perm_stmt)
                for perm_id in perm_ids:
                    session.add(RolePermission(role_id=role, permission_id=perm_id))
            session.commit()
    print("Default Permission Assigned")


def default_global_setting():
    with SyncSessionFactory() as session:
        stmt = select(func.count(GlobalConfig.id))
        config = session.execute(stmt).scalar_one()
        if config == 0:
            session.add(GlobalConfig())
            session.commit()
