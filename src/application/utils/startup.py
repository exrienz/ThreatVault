import logging

from sqlalchemy import func, select
from sqlalchemy_utils import create_database, database_exists

from src.config import default_permissions, default_role_permission, default_roles
from src.domain.entity import Base, GlobalConfig, Role
from src.domain.entity.user_access import Permission, RolePermission
from src.infrastructure.database import SyncSessionFactory, sync_db_conn, sync_engine

from .plugin import upload_builtin_plugin

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def startup_db():
    logger.info("Creating DB")
    if not database_exists(sync_db_conn):
        create_database(sync_db_conn)
    Base.metadata.create_all(bind=sync_engine)

    logger.info("DB Created")

    create_default_roles()
    default_global_setting()
    upload_builtin_plugin(logger)
    creating_default_permission()
    create_role_permissions()


def create_default_roles():
    logger.info("Creating Default Role")
    with SyncSessionFactory() as session:
        for data in default_roles:
            role_name = data.get("name")
            exists = session.scalar(select(Role).where(Role.name == role_name))

            if exists:
                exists.super_admin = data.get("super_admin", False)
                exists.required_project_access = data.get(
                    "required_project_access", True
                )
            else:
                session.add(Role(**data))

        session.commit()

    logger.info("Default Role Created")


def creating_default_permission():
    logger.info("Creating Default Permissions")
    # TODO: UPDATE
    with SyncSessionFactory() as session:
        stmt = select(func.count(Permission.id))
        perm = session.execute(stmt).scalar_one()
        if perm == 0:
            role_list = [Permission(**data) for data in default_permissions]
            session.add_all(role_list)
            session.commit()
    logger.info("Default Permission Created")


def create_role_permissions():
    logger.info("Assinging Default Permissions")
    with SyncSessionFactory() as session:
        stmt = select(func.count(RolePermission.id))
        perm = session.execute(stmt).scalar_one()
        if perm != 0:
            return

        for data in default_role_permission:
            role_name = data.get("role")
            scopes = data.get("scopes")

            role_id = session.scalar(select(Role.id).where(Role.name == role_name))
            if not role_id:
                continue

            perm_ids = session.scalars(
                select(Permission.id).where(Permission.scope.in_(scopes))
            ).all()

            for perm_id in perm_ids:
                exists = session.scalar(
                    select(RolePermission.id).where(
                        RolePermission.role_id == role_id,
                        RolePermission.permission_id == perm_id,
                    )
                )

                if not exists:
                    session.add(RolePermission(role_id=role_id, permission_id=perm_id))
            session.commit()
    logger.info("Default Permission Assigned")


def default_global_setting():
    with SyncSessionFactory() as session:
        stmt = select(func.count(GlobalConfig.id))
        config = session.execute(stmt).scalar_one()
        if config == 0:
            default = {
                "sla_critical": 120,
                "sla_high": 90,
                "sla_medium": 60,
                "sla_low": 30,
            }
            session.add(GlobalConfig(**default))
            session.commit()
