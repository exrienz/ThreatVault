from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Project(Base):
    __tablename__ = "project"

    name: Mapped[str]
    type_: Mapped[str] = mapped_column("type")
    creator_id: Mapped[UUID]

    environment = relationship(
        "Environment",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Environment(Base):
    __tablename__ = "environment"

    name: Mapped[str]
    project_id: Mapped[UUID] = mapped_column(ForeignKey("project.id"))

    project = relationship("Project")
    products = relationship(
        "Product", back_populates="environment", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "product"

    name: Mapped[str]
    newFindingTracker: Mapped[bool] = mapped_column(default=False)
    allowAsyncUpdate: Mapped[bool] = mapped_column(default=False)
    weEscalation: Mapped[bool] = mapped_column(default=False)
    moEscalation: Mapped[bool] = mapped_column(default=False)
    apiKey: Mapped[Optional[str]]

    environment_id: Mapped[UUID] = mapped_column(ForeignKey("environment.id"))
    environment = relationship("Environment", back_populates="products")

    accesses = relationship(
        "ProductUserAccess", back_populates="products", cascade="all, delete-orphan"
    )


#
class ProductEscalationPoint(Base):
    __tablename__ = "product_escalation_point"
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_user.id", ondelete="CASCADE")
    )
