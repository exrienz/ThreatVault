import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDashboardE2E:
    async def test_dashboard_without_login(self, async_client: AsyncClient):
        response = await async_client.get("/")
        assert response.status_code == 401

    # async def test_admin_dashboard(self, admin_client: AsyncClient):
    #     response = await admin_client.get("/")
    #     assert response.status_code == 200
    #
    # async def test_itse_dashboard(self, itse_client: AsyncClient):
    #     response = await itse_client.get("/")
    #     assert response.status_code == 200
    #
    # async def test_manager_dashboard(self, manager_client: AsyncClient):
    #     response = await manager_client.get("/")
    #     assert response.status_code == 307

    async def test_audit_dashboard(self, audit_client: AsyncClient):
        response = await audit_client.get("/")
        assert response.status_code == 200

    # @pytest.mark.asyncio
    # async def test_owner_dashboard(self, owner_client: AsyncClient):
    #     response = await owner_client.get("/")
    #     assert response.status_code == 200
