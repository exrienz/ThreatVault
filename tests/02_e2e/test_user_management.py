import pytest
from bs4 import BeautifulSoup
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistence.user import UserRepository
from tests.helper import get_user_by_role


class TestUserManagementE2E:
    @pytest.mark.parametrize(
        "request_fixture, expected_status",
        [
            pytest.param("async_client", 401, id="unauthenticated"),
            pytest.param("admin_client", 200, id="admin"),
            pytest.param("itse_client", 200, id="itse"),
            pytest.param("audit_client", 403, id="audit"),
            pytest.param("owner_client", 403, id="owner"),
        ],
        indirect=["request_fixture"],
    )
    async def test_view_user_management(
        self, request_fixture: AsyncClient, expected_status: int
    ):
        urls = ["/manage-user/", "/manage-owner", "manage-api"]
        for url in urls:
            response = await request_fixture.get(url)
            assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "request_fixture, expected_status",
        [
            pytest.param("async_client", 401, id="unauthenticated"),
            pytest.param("admin_client", 200, id="admin"),
            pytest.param("itse_client", 403, id="itse"),
            pytest.param("audit_client", 403, id="audit"),
            pytest.param("owner_client", 403, id="owner"),
        ],
        indirect=["request_fixture"],
    )
    async def test_view_role_management(
        self, request_fixture: AsyncClient, expected_status: int
    ):
        response = await request_fixture.get("/manage-role")
        assert response.status_code == expected_status

    async def test_itse_cannot_view_manage_column(self, itse_client: AsyncClient):
        response = await itse_client.get("/manage-user/")
        assert response.status_code == 200

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table")
        assert table, "Table is not found"

        thead_row = table.find("thead").find("tr")
        assert thead_row, "No thead found in table"

        headers = [th.get_text(strip=True) for th in thead_row.find_all("th")]

        assert len(headers) == 5, f"Expected 5 columns, got {len(headers)}"
        assert headers[-1] != "Manage"

    async def test_admin_view_manage_column(self, admin_client: AsyncClient):
        response = await admin_client.get("/manage-user/")
        assert response.status_code == 200

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table")
        assert table, "Table is not found"

        thead_row = table.find("thead").find("tr")
        assert thead_row, "No thead found in table"

        headers = [th.get_text(strip=True) for th in thead_row.find_all("th")]

        assert len(headers) == 6, f"Expected 5 columns, got {len(headers)}"
        assert headers[-1] == "Manage"

    async def test_itse_cannot_manage_user(
        self, session: AsyncSession, itse_client: AsyncClient
    ):
        repo = UserRepository(session)

        manager = await repo.get_first_by_filter(
            {"username": "manager"}, ["created_at"]
        )
        if manager is None:
            pytest.skip("User named manager didn't exists!")
        response = await itse_client.get(f"/manage-user/user/{manager.id}")
        assert response.status_code == 403

    async def test_admin_manage_user(
        self, session: AsyncSession, admin_client: AsyncClient
    ):
        manager = await UserRepository(session).get_first_by_filter(
            {"username": "manager"}, ["created_at"]
        )
        if manager is None:
            pytest.skip("User named manager didn't exists!")
        manager_id = manager.id
        response = await admin_client.get(f"/manage-user/user/{manager.id}")
        assert response.status_code == 200

        response = await admin_client.put(
            f"/manage-user/user/{manager.id}",
            data={"active": False, "role_id": manager.role_id},
        )
        assert response.status_code == 200

        session.expire_all()
        manager = await UserRepository(session).get_by_id(manager_id)

        assert manager is not None
        assert not manager.active

        # Reset
        response = await admin_client.put(
            f"/manage-user/user/{manager.id}",
            data={"active": True, "role_id": manager.role_id},
        )
        assert response.status_code == 200
