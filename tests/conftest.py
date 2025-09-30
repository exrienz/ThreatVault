import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool, create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.entity import Base
from src.infrastructure.database.session import get_session
from src.main import app
from tests.factories.role import RoleFactory
from tests.factories.user import UserFactory
from tests.fixtures.authorization import (  # noqa: F401
    admin_client,
    audit_client,
    create_users,
    itse_client,
    manager_client,
    owner_client,
)

TEST_DATABASE = "sentineltest"
conn_uri = f"postgresql+asyncpg://root:secret@localhost:5432/{TEST_DATABASE}"
engine = create_async_engine(conn_uri, echo=False, poolclass=NullPool)

conn_sync_uri = "postgresql+psycopg2://root:secret@localhost:5432"
admin_engine = create_engine(conn_sync_uri, isolation_level="AUTOCOMMIT")
sync_engine = create_engine(f"{conn_sync_uri}/{TEST_DATABASE}")

pytestmark = pytest.mark.asyncio


def create_table():
    with admin_engine.connect() as connection:
        try:
            connection.execute(text(f"CREATE DATABASE {TEST_DATABASE};"))
        except ProgrammingError:
            print("Error creating database, might already exists!")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    create_table()
    Base.metadata.create_all(bind=sync_engine)
    generate_users()
    yield
    # Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture(scope="session", autouse=True)
def configure_app_for_tests():
    app.state.testing = True
    yield
    app.state.testing = False


def generate_users():
    with sessionmaker(bind=sync_engine)() as session:
        try:
            create_users(session)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


@pytest_asyncio.fixture(name="session")
async def session_fixture():
    # async_session = async_sessionmaker(bind=engine)

    async_session = async_sessionmaker(bind=engine)
    async with async_session() as session:
        await session.begin()
        yield session
        await session.rollback()

    # async_session = async_sessionmaker(bind=engine)()
    # try:
    #     yield async_session
    # except Exception:
    #     await async_session.rollback()
    #     raise
    # finally:
    #     await async_session.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def session_override():
    async_session = async_sessionmaker(bind=engine)

    async def get_db_override():
        async with async_session() as session:
            await session.begin()
            yield session
            await session.rollback()

    app.dependency_overrides[get_session] = get_db_override
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def set_session_for_factories(session: Session):
    RoleFactory._meta.sqlalchemy_session = session
    UserFactory._meta.sqlalchemy_session = session
