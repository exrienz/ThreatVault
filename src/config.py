import json

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DB_URL: AnyUrl = AnyUrl("user:pass@localhost:5432/foobar")
    SYNC_DB_DRIVER: str = "postgresql+psycopg2"
    ASYNC_DB_DRIVER: str = "postgresql+asyncpg"


settings = Settings()

default_roles = []
with open("src/default_roles.json") as file:
    default_roles = json.load(file)

sidebar_items = []
with open("src/sidebars.json") as file:
    sidebar_items = json.load(file)
