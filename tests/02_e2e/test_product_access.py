import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.product import ProductFactory, ProductUserAccessFactory

from tests.helper import get_user_by_role


class TestProductAccessE2E:
    @pytest.mark.parametrize(
        "request_fixture, expected_status",
        [
            pytest.param("async_client", 401, id="unauthenticated"),
            pytest.param("admin_client", 200, id="admin"),
            pytest.param("itse_client", 200, id="itse"),
            pytest.param("manager_client", 200, id="manager"),
            pytest.param("audit_client", 404, id="audit"),
            pytest.param("owner_client", 404, id="owner"),
        ],
        indirect=["request_fixture"],
    )
    async def test_product_access_default(
        self, session: AsyncSession, request_fixture: AsyncClient, expected_status: int
    ):
        admin = await get_user_by_role(session, "Admin")
        if admin is None:
            pytest.skip("Admin does not exists!")
        product = await ProductFactory.create_async(
            session, environment__project__creator_id=admin.id
        )
        response = await request_fixture.get(f"/product/{product.id}")
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "request_fixture, role",
        [
            pytest.param("audit_client", "Audit", id="audit"),
            pytest.param("owner_client", "Owner", id="owner"),
        ],
        indirect=["request_fixture"],
    )
    async def test_product_access_given_access(
        self,
        session: AsyncSession,
        request_fixture: AsyncClient,
        role: str,
    ):
        admin = await get_user_by_role(session, "Admin")
        if admin is None:
            pytest.skip("Admin does not exists!")
        product = await ProductFactory.create_async(
            session, environment__project__creator_id=admin.id
        )
        user = await get_user_by_role(session, role)
        if user is None:
            pytest.skip("User does not exists!")

        await ProductUserAccessFactory.create_async(
            session, user_id=user.id, product_id=product.id
        )
        response = await request_fixture.get(f"/product/{product.id}")
        assert response.status_code == 200
