import pytest
from httpx import AsyncClient


class TestDashboardE2E:
    @pytest.mark.parametrize(
        "request_fixture, expected_status",
        [
            pytest.param("async_client", 401, id="unauthenticated"),
            pytest.param("admin_client", 200, id="admin"),
            pytest.param("itse_client", 200, id="itse"),
            pytest.param("audit_client", 200, id="audit"),
            pytest.param("owner_client", 200, id="owner"),
            pytest.param("manager_client", 307, id="manager"),
        ],
        indirect=["request_fixture"],
    )
    async def test_access_dashboard(
        self, request_fixture: AsyncClient, expected_status: int
    ):
        response = await request_fixture.get("/")
        assert response.status_code == expected_status
