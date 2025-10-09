from httpx import AsyncClient


class TestAuthE2E:
    async def test_dashboard_without_login(self, async_client: AsyncClient):
        response = await async_client.get("/")
        assert response.status_code == 401
