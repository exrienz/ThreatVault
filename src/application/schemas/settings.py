from typing import Optional

from pydantic import BaseModel


class GlobalConfigSchema(BaseModel):
    site_name: Optional[str] = None
    site_domain: Optional[str] = None
    site_logo_url: Optional[str] = None

    sla_critical: Optional[int]
    sla_high: Optional[int]
    sla_medium: Optional[int]
    sla_low: Optional[int]

    login_via_email: Optional[bool] = False

    okta_enabled: Optional[bool] = False
    okta_domain: Optional[str] = None
    okta_client_id: Optional[str] = None
    okta_client_secret: Optional[str] = None

    smtp_server: Optional[str]
    smtp_port: Optional[str]
    smtp_username: Optional[str]
    smtp_password: Optional[str]

    sensitive_hosts: Optional[str]

    llm_url: Optional[str]
    llm_api_key: Optional[str]
    llm_model: Optional[str]
