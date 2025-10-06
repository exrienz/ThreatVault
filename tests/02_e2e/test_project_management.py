import pytest
from bs4 import BeautifulSoup
from httpx import AsyncClient


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
    async def test_create_project(self, itse_client: AsyncClient, project_type: str):
        project_name = f"pytest-project-{project_type}"
        response = await itse_client.post(
            "/project-management/",
            data={"name": project_name, "project_type": project_type},
        )

        assert response.status_code == 200

        response = await itse_client.get(f"/project-management?type_={project_type}")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        created_project = soup.select_one(".accordion-button .text-wrap").get_text(
            strip=True
        )

        assert created_project == project_name

    @pytest.mark.parametrize(
        "project_type", [pytest.param("VA", id="VA"), pytest.param("HA", id="HA")]
    )
    async def test_create_product(self, itse_client: AsyncClient, project_type: str):
        response = await itse_client.get(f"/project-management?type_={project_type}")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        project = soup.select_one(".accordion-item")
        assert project is not None
        project_id = project["id"].replace("id_accordion_proj_", "")

        product_name = f"pytest-product-{project_type}"
        response = await itse_client.post(
            "/project-management/product",
            data={
                "name": product_name,
                "project_id": project_id,
                "environment_name": "all",
            },
        )

        assert response.status_code == 200

        response = await itse_client.get(f"/project-management?type_={project_type}")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")
        project = soup.select_one(".accordion-item")

        production_products = [
            li.get_text(strip=True)
            for li in project.select("ul:has(li:contains('Production')) li a")
        ]
        non_production_products = [
            li.get_text(strip=True)
            for li in project.select("ul:has(li:contains('Non-Production')) li a")
        ]
        assert product_name in production_products, f"{product_name} not in Production"
        assert product_name in non_production_products, (
            f"{product_name} not in Non-Production"
        )

    @pytest.mark.parametrize(
        "project_type", [pytest.param("VA", id="VA"), pytest.param("HA", id="HA")]
    )
    async def test_delete_product(self, itse_client: AsyncClient, project_type: str):
        response = await itse_client.get(f"/project-management?type_={project_type}")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")
        project = soup.select_one(".accordion-item")

        non_prod_li = project.select_one(
            "ul:has(li:contains('Non-Production')) li[id^='id_prod_accordion_']"
        )
        assert non_prod_li is not None, "Non-Production product does not exists"

        non_prod_id = non_prod_li["id"].replace("id_prod_accordion_", "")
        assert non_prod_id != "", (
            "Non-Production is an empty string. Should be prefixed with id_prod_accordion_"  # noqa: E501
        )

        response = await itse_client.delete(
            "/project-management/product", params={"product_id": non_prod_id}
        )
        assert response.status_code == 200

        response = await itse_client.get(f"/product/{non_prod_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "project_type", [pytest.param("VA", id="VA"), pytest.param("HA", id="HA")]
    )
    async def test_delete_project(self, itse_client: AsyncClient, project_type: str):
        response = await itse_client.get(f"/project-management?type_={project_type}")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        project = soup.select_one(".accordion-item")
        assert project is not None, "No Project Created"

        project_id = project["id"].replace("id_accordion_proj_", "")
        assert project_id != "", (
            "Non-Production is an empty string. Should be prefixed with id_accordion_proj_"  # noqa: E501
        )

        response = await itse_client.delete(
            "/project-management/", params={"project_id": project_id}
        )
        assert response.status_code == 200

        response = await itse_client.get(f"/project/{project_id}")
        assert response.status_code == 404
