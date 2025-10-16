import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.product import EnvironmentFactory, ProductFactory, ProjectFactory
from tests.helper import (
    get_product_by_id,
    get_project_by_project_name,
)


class TestProjectManagementE2E:
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
    async def test_view_project_management(
        self, request_fixture: AsyncClient, expected_status: int
    ):
        urls = ["/project-management", "/project-management?type_=HA"]
        for url in urls:
            response = await request_fixture.get(url)
            assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "project_type", [pytest.param("VA", id="VA"), pytest.param("HA", id="HA")]
    )
    async def test_create_project(
        self, session: AsyncSession, itse_client: AsyncClient, project_type: str
    ):
        project_name = f"pytest-project-{project_type}"
        response = await itse_client.post(
            "/project-management/",
            data={"name": project_name, "project_type": project_type},
        )

        assert response.status_code == 200

        response = await itse_client.get(f"/project-management?type_={project_type}")
        assert response.status_code == 200

        project = await get_project_by_project_name(session, project_name)
        assert project is not None, "Project does not created!"
        assert project.name == project_name

    @pytest.mark.parametrize(
        "project_type", [pytest.param("VA", id="VA"), pytest.param("HA", id="HA")]
    )
    async def test_create_product(
        self, session: AsyncSession, itse_client: AsyncClient, project_type: str
    ):
        project = await ProjectFactory.create_async(session)
        await EnvironmentFactory.create_async(
            session, name="production", project=project
        )
        await EnvironmentFactory.create_async(
            session, name="non-production", project=project
        )

        product_name = f"pytest-product-{project_type}"
        response = await itse_client.post(
            "/project-management/product",
            data={
                "name": product_name,
                "project_id": project.id,
                "environment_name": "all",
            },
        )

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "project_type", [pytest.param("VA", id="VA"), pytest.param("HA", id="HA")]
    )
    async def test_delete_product(
        self, session: AsyncSession, itse_client: AsyncClient, project_type: str
    ):
        project = await ProjectFactory.create_async(session, type_=project_type)
        product = await ProductFactory.create_async(
            session, environment__project=project
        )
        response = await itse_client.delete(
            f"/project-management/product?product_id={product.id}"
        )
        assert response.status_code == 200

        product_db = await get_product_by_id(session, product.id)
        assert product_db is None

    @pytest.mark.parametrize(
        "project_type", [pytest.param("VA", id="VA"), pytest.param("HA", id="HA")]
    )
    async def test_delete_project(
        self, session: AsyncSession, itse_client: AsyncClient, project_type: str
    ):
        project = await ProjectFactory.create_async(session, type_=project_type)
        response = await itse_client.delete(
            "/project-management/", params={"project_id": project.id}
        )
        assert response.status_code == 200

        response = await itse_client.get(f"/project/{project.id}")
        assert response.status_code == 404
