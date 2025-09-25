from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class EmailConfig(Base):
    __tablename__ = "email_config"

    server: Mapped[str]
    port: Mapped[str]
    username: Mapped[str]
    password: Mapped[str]


class GlobalConfig(Base):
    __tablename__ = "global_config"

    site_name: Mapped[Optional[str]]
    site_domain: Mapped[Optional[str]]
    site_logo_url: Mapped[Optional[str]]
    sla_critical: Mapped[int] = mapped_column(default=0)
    sla_high: Mapped[int] = mapped_column(default=0)
    sla_medium: Mapped[int] = mapped_column(default=0)
    sla_low: Mapped[int] = mapped_column(default=0)

    login_via_email: Mapped[bool] = mapped_column(server_default="t")

    okta_enabled: Mapped[Optional[bool]] = mapped_column(server_default="f")
    okta_domain: Mapped[Optional[str]]
    okta_client_id: Mapped[Optional[str]]
    okta_client_secret: Mapped[Optional[str]]
    okta_redirect_url: Mapped[Optional[str]]

    smtp_server: Mapped[Optional[str]]
    smtp_port: Mapped[Optional[str]]
    smtp_username: Mapped[Optional[str]]
    smtp_password: Mapped[Optional[str]]
    smtp_tls: Mapped[Optional[bool]] = mapped_column(server_default="t")

    sensitive_hosts: Mapped[Optional[str]]

    llm_url: Mapped[Optional[str]]
    llm_api_key: Mapped[Optional[str]]
    llm_model: Mapped[Optional[str]]
