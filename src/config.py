import json
import re
from datetime import timedelta

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DB_URL: AnyUrl = AnyUrl("user:pass@localhost:5432/foobar")
    SYNC_DB_DRIVER: str = "postgresql+psycopg2"
    ASYNC_DB_DRIVER: str = "postgresql+asyncpg"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRED_MINUTES: int = 720
    JWT_EXPIRED_DELTA: timedelta = timedelta(minutes=JWT_EXPIRED_MINUTES)

    SESSION_SECRET_KEY: str = "SESSION_SECRET_KEY"
    NEWEST_CVE_URL: str = "https://www.tenable.com/cve/feeds?sort=newest"


settings = Settings()

default_roles = []
with open("src/default/roles.json") as file:
    default_roles = json.load(file)

sidebar_items = []
with open("src/default/sidebars.json") as file:
    sidebar_items = json.load(file)

version = None
with open("./CHANGELOG.md", encoding="utf-8") as f:
    content = f.read()
    match = re.search(r"^##\s*\[(.*?)\]", content, re.MULTILINE)
    if match:
        version = match.group(1)

default_permissions = []
with open("src/default/permissions.json") as file:
    default_permissions = json.load(file)

default_role_permission = []
with open("src/default/role_permission.json") as file:
    default_role_permission = json.load(file)
