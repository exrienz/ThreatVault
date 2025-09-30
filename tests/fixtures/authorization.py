import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session

from src.application.security.oauth2.password import pwd_context
from src.domain.entity import Role, User
from src.domain.entity.user_access import Permission, RolePermission

password = "Password@123"
password_hash = pwd_context.hash(password)

roles = {
    "admin": [Role(name="admin", super_admin=True, required_project_access=False), []],
    "itse": [Role(name="ITSE", required_project_access=False), []],
    "manager": [Role(name="manager", required_project_access=False), []],
    "owner": [Role(name="owner"), ["comment:create", "dashboard:view"]],
    "audit": [Role(name="audit"), ["dashboard:view"]],
}
permission_list = ["dashboard:view", "comment:create"]


def create_permissions(session: Session):
    permissions: dict[str, Permission] = {}
    for permission in permission_list:
        perm = Permission(name=permission, scope=permission, url="")
        session.add(perm)
        session.commit()
        session.refresh(perm)
        permissions[permission] = perm
    return permissions


def create_users(session: Session):
    permissions = create_permissions(session)
    users = []
    for name, (role, perm) in roles.items():
        session.add(role)
        session.commit()
        session.refresh(role)

        user = User(
            username=name,
            email=f"{name}@sentinel-test.com",
            password=password_hash,
            role_id=role.id,
            active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        users.append(user)

        # assign perm
        role_perms = []
        for v in perm:
            permission = permissions.get(v)
            if permission is None:
                continue
            role_perms.append(
                RolePermission(role_id=role.id, permission_id=permission.id)
            )
        session.add_all(role_perms)
        session.commit()
    return users


@pytest_asyncio.fixture(scope="function")
async def admin_client(async_client: AsyncClient):
    data = {"username": "admin", "password": password}
    login_response = await async_client.post("/auth/login", data=data)
    assert login_response.status_code == 200

    async_client.cookies.update(login_response.cookies)

    yield async_client


@pytest_asyncio.fixture(scope="function")
async def itse_client(async_client: AsyncClient):
    data = {"username": "itse", "password": password}
    login_response = await async_client.post("/auth/login", data=data)
    assert login_response.status_code == 200

    async_client.cookies.update(login_response.cookies)

    yield async_client


@pytest_asyncio.fixture(scope="function")
async def manager_client(async_client: AsyncClient):
    data = {"username": "manager", "password": password}
    login_response = await async_client.post("/auth/login", data=data)
    assert login_response.status_code == 200

    async_client.cookies.update(login_response.cookies)

    yield async_client


@pytest_asyncio.fixture(scope="function")
async def owner_client(async_client: AsyncClient):
    data = {"username": "owner", "password": password}
    login_response = await async_client.post("/auth/login", data=data)
    assert login_response.status_code == 200

    async_client.cookies.update(login_response.cookies)

    yield async_client


@pytest_asyncio.fixture(scope="function")
async def audit_client(async_client: AsyncClient):
    data = {"username": "audit", "password": password}
    login_response = await async_client.post("/auth/login", data=data)
    assert login_response.status_code == 200

    async_client.cookies.update(login_response.cookies)

    yield async_client
