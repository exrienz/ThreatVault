import http.client
import json
import urllib.parse

from fastapi import Depends

from src.persistence import GlobalRepository


class OKTAExternalService:
    def __init__(self, repository: GlobalRepository = Depends()):
        self.repository = repository
        self.domain = None

    async def _get_config(self) -> dict:
        data = await self.repository.get()
        if data is None:
            raise
        if data.okta_domain is None:
            raise
        self.domain = data.okta_domain
        return {
            "domain": data.okta_domain,
            "client_id": data.okta_client_id,
            "client_secret": data.okta_client_secret,
        }

    async def _get_token(self) -> tuple[str, str]:
        config = await self._get_config()
        domain = config.get("domain")
        if domain is None:
            raise
        domain = domain.replace("https://", "").replace("http://", "").strip("/")
        conn = http.client.HTTPSConnection(domain)
        payload = {
            "audience": f"https://{domain}/api/v2/",
            "grant_type": "client_credentials",
            **config,
        }
        headers = {"content-type": "application/json"}
        conn.request("POST", "/oauth/token", json.dumps(payload), headers)

        res = conn.getresponse()
        data = res.read()

        data_raw = data.decode("utf-8")
        token_dict: dict = json.loads(data_raw)
        access_token = token_dict.get("access_token")
        token_type = token_dict.get("token_type")
        return f"{token_type} {access_token}", domain

    async def get_users(self, name: str | None = None, page: int = 1):
        token, domain = await self._get_token()
        conn = http.client.HTTPSConnection(domain)
        headers = {"authorization": token}
        base_params = {"fields": "email,nickname", "include_fields": "true"}
        query = {
            "search_engin": "v3",
            "page": page - 1,
            "per_page": 10,
            "include_totals": "true",
        }
        if name:
            query["q"] = f"name:{name}*"
        all_params = {**base_params, **query}
        params = urllib.parse.urlencode(all_params)
        conn.request("GET", f"/api/v2/users?{params}", headers=headers)
        res = conn.getresponse()
        if res.status != 200:
            raise
        data = res.read().decode()
        return json.loads(data)
