from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "auth_user"

    email: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    active: Mapped[bool] = mapped_column(server_default="f")

    role_id: Mapped[UUID] = mapped_column(ForeignKey("role.id"))
    role = relationship("Role", back_populates="users")


class Role(Base):
    __tablename__ = "role"

    name: Mapped[str]
    super_admin: Mapped[bool] = mapped_column(server_default="f")
    required_project_access: Mapped[bool] = mapped_column(server_default="t")
    users = relationship("User", back_populates="role")


class Permission(Base):
    __tablename__ = "permission"

    name: Mapped[str]
    scope: Mapped[str]
    url: Mapped[str]


class RolePermission(Base):
    __tablename__ = "role_permission"

    role_id: Mapped[UUID] = mapped_column(ForeignKey("role.id"))
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permission.id"))


class ProductUserAccess(Base):
    __tablename__ = "product_user_access"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("auth_user.id"))
    product_id: Mapped[UUID] = mapped_column(ForeignKey("product.id"))
    granted: Mapped[bool] = mapped_column(server_default="f")
