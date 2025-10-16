import os
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.finding import Plugin
from tests.helper import toastMatcher


class TestPluginManagementE2E:
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
    async def test_plugin_management_view(
        self, request_fixture: AsyncClient, expected_status: int
    ):
        response = await request_fixture.get("/setting/plugin/")
        assert response.status_code == expected_status

    async def test_upload_plugin_success(
        self, session: AsyncSession, admin_client: AsyncClient
    ):
        data = {
            "description": "Test plugin upload",
            "config": "",
            "active": "true",
            "env": "VA",
        }
        name = "test_plugin"
        with open("./plugins/builtin/va/nessus.py", "rb") as f:
            files = [
                (
                    "file",
                    (f"{name}.py", f.read(), "text/x-python"),
                ),
            ]

            response = await admin_client.post(
                "/setting/plugin/create", data=data, files=files
            )
            assert response.status_code == 200

        query = await session.execute(
            select(Plugin).where(Plugin.type == "custom", Plugin.name == name)
        )
        plugin = query.scalar_one_or_none()
        assert plugin is not None, f"Plugin with name: {name}, should be uploaded!"

    async def test_upload_plugin_wrong_extension_fail(
        self, session: AsyncSession, admin_client: AsyncClient
    ):
        data = {
            "description": "Test plugin upload",
            "config": "",
            "active": "true",
            "env": "VA",
        }
        name = "test_plugin_fail"
        with open("./plugins/builtin/va/nessus.py", "rb") as f:
            files = [
                (
                    "file",
                    (f"{name}.txt", f.read(), "text/x-python"),
                ),
            ]

            response = await admin_client.post(
                "/setting/plugin/create",
                data=data,
                files=files,
            )

            assert response.status_code == 422
            err_msg = toastMatcher(response.text)
            assert err_msg == "Expected file format: Required .py"
        query = await session.execute(
            select(Plugin).where(Plugin.type == "custom", Plugin.name == name)
        )
        plugin = query.scalar_one_or_none()
        assert plugin is None, f"Plugin with name: {name}, should not be uploaded!"

    async def test_upload_plugin_create_same_plugin_fail(
        self, admin_client: AsyncClient
    ):
        data = {
            "description": "Test plugin upload",
            "config": "",
            "active": "true",
            "env": "VA",
        }
        name = "test_plugin"
        with open("./plugins/builtin/va/nessus.py", "rb") as f:
            files = [
                (
                    "file",
                    (f"{name}.txt", f.read(), "text/x-python"),
                ),
            ]

            response = await admin_client.post(
                "/setting/plugin/create",
                data=data,
                files=files,
            )
            assert response.status_code == 422
            err_msg = toastMatcher(response.text)
            assert (
                err_msg
                == f"Expected file format: Filename: {name} with type VA already exists"
            )

    async def test_verity_plugin_success(
        self, session: AsyncSession, admin_client: AsyncClient
    ):
        name = "test_plugin"
        query = await session.execute(
            select(Plugin).where(Plugin.type == "custom", Plugin.name == name)
        )
        plugin = query.scalar_one_or_none()
        assert plugin is not None, "Required plugin does not exists!"

        data = {"use_to_verify": "true", "type_": "VA"}

        file_path = "./tests/files/va_valid.csv"
        if not os.path.exists(file_path):
            pytest.skip(f"Skipping test: missing file {file_path}")

        with open(file_path, "rb") as f:
            files = [
                (
                    "file",
                    (f"{name}.csv", f.read(), "text/csv"),
                ),
            ]

            response = await admin_client.post(
                f"/setting/plugin/verify/{plugin.id}",
                data=data,
                files=files,
            )
            assert response.status_code == 200

            msg = toastMatcher(response.text)
            assert msg == f"Plugin Verified: {name}"

    async def test_verify_plugin_fail(
        self, session: AsyncSession, admin_client: AsyncClient
    ):
        query = await session.execute(
            select(Plugin).where(Plugin.type == "builtin", Plugin.name == "manual")
        )
        plugin = query.scalar_one_or_none()
        assert plugin is not None

        data = {"use_to_verify": "true", "type_": "VA"}

        file_path = "./tests/files/va_valid.csv"
        if not os.path.exists(file_path):
            pytest.skip(f"Skipping test: missing file {file_path}")

        with open(file_path, "rb") as f:
            files = [
                (
                    "file",
                    ("manual.csv", f.read(), "text/csv"),
                ),
            ]

            response = await admin_client.post(
                f"/setting/plugin/verify/{plugin.id}",
                data=data,
                files=files,
            )
            assert response.status_code == 422
            msg = toastMatcher(response.text)
            assert msg == "Plugin didn&#39;t match the file uploaded!"
