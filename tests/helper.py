import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.domain.entity.project_management import Product, Project
from src.domain.entity.user_access import Role, User
from uuid import UUID


async def get_role_by_name(session: AsyncSession, name: str) -> Role | None:
    stmt = select(Role).filter_by(name=name)
    return await session.scalar(stmt)


async def get_user_by_role(session: AsyncSession, role_name: str) -> User | None:
    stmt = select(User).join(Role).where(Role.name == role_name)
    return await session.scalar(stmt)


async def get_project_by_project_name(
    session: AsyncSession, project_name: str
) -> Project | None:
    stmt = select(Project).where(Project.name == project_name)
    return await session.scalar(stmt)


async def get_product_by_id(
    session: AsyncSession,
    product_id: UUID,
) -> Product | None:
    stmt = select(Product).where(Product.id == product_id)
    return await session.scalar(stmt)


def toastMatcher(html: str):
    match = re.search(r"ToastCustom\(`(.*?)`,\s*\".*?\"\)", html)
    if match:
        return match.group(1)
    return None
