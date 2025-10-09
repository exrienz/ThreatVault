from authlib.integrations.starlette_client import OAuth
from fastapi import Depends

from src.domain.entity.setting import GlobalConfig
from src.persistence.config import GlobalRepository

oauth = OAuth()


# TODO: Registry pattern
class OpenIDConnectService:
    def __init__(self, repository: GlobalRepository = Depends()):
        self.repository = repository
        self.kc = None

    async def get_config(self) -> GlobalConfig:
        config = await self.repository.get()
        if config is None:
            raise
        if not config.okta_enabled:
            raise
        return config

    def register(self, name: str, client_id: str, client_secret: str, domain: str):
        oauth.register(
            name,
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url=f"https://{domain}/.well-known/openid-configuration",
            client_kwargs={"scope": "openid profile email"},
        )

    # TODO: Deprecate this in favor of registry pattern
    async def configure(self):
        config = await self.get_config()
        self.register(
            "okta",
            config.okta_client_id or "",
            config.okta_client_secret or "",
            config.okta_domain or "",
        )

    async def get_oauth(self):
        return oauth
