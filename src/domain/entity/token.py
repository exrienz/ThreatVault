from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Token(Base):
    __tablename__ = "api_token"

    token: Mapped[str]
    name: Mapped[str]
    creator_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("auth_user.id"))

    creator = relationship("User")
