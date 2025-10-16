import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.schemas.settings import GlobalConfigSchema
from src.domain.entity.setting import GlobalConfig


class TestConfigE2E:
    @pytest.mark.parametrize(
        "request_fixture, expected_status",
        [
            pytest.param("async_client", 401, id="unauthenticated"),
            pytest.param("admin_client", 200, id="admin"),
            pytest.param("itse_client", 403, id="itse"),
            pytest.param("manager_client", 403, id="manager"),
            pytest.param("audit_client", 403, id="audit"),
            pytest.param("owner_client", 403, id="owner"),
        ],
        indirect=["request_fixture"],
    )
    async def test_config_page_access(
        self, request_fixture: AsyncClient, expected_status: int
    ):
        response = await request_fixture.get("/setting")
        assert response.status_code == expected_status

    async def test_admin_update_success(
        self, session: AsyncSession, admin_client: AsyncClient
    ):
        query = await session.execute(select(GlobalConfig))
        config = query.scalar_one_or_none()
        assert config is not None
        assert config.sla_critical == 30

        update_data = GlobalConfigSchema(sla_critical=60)
        response = await admin_client.post("/setting", data=update_data.model_dump())

        assert response.status_code == 200

        session.expire_all()
        query = await session.execute(select(GlobalConfig))
        config = query.scalar_one_or_none()
        assert config is not None
        assert config.sla_critical == 60
