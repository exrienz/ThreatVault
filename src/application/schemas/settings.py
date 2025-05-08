from typing import Optional

from pydantic import BaseModel


class GlobalConfigSchema(BaseModel):
    site_name: Optional[str]
    site_domain: Optional[str]
    site_logo_url: Optional[str]

    sla_critical: Optional[int]
    sla_high: Optional[int]
    sla_medium: Optional[int]
    sla_low: Optional[int]

    login_via_email: Optional[bool] = False

    okta_enabled: Optional[bool] = False
    okta_domain: Optional[str]
    okta_client_id: Optional[str]
    okta_client_secret: Optional[str]

    smtp_server: Optional[str]
    smtp_port: Optional[str]
    smtp_username: Optional[str]
    smtp_password: Optional[str]


class UserResetPasswordSchema(BaseModel):
    current_pass: str
    new_pass: str
    confirm_pass: str
