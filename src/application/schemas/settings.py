from typing import Optional

from pydantic import BaseModel


class GlobalConfigSchema(BaseModel):
    site_name: Optional[str] = None
    site_domain: Optional[str] = None
    site_logo_url: Optional[str] = None

    sla_critical: Optional[int] = 30
    sla_high: Optional[int] = 60
    sla_medium: Optional[int] = 90
    sla_low: Optional[int] = 120

    login_via_email: Optional[bool] = False

    okta_enabled: Optional[bool] = False
    okta_domain: Optional[str] = None
    okta_client_id: Optional[str] = None
    okta_client_secret: Optional[str] = None

    smtp_server: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: Optional[bool] = False

    sensitive_hosts: Optional[str] = None

    llm_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
