import factory
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import Product, Environment, Project
from src.domain.entity.user_access import ProductUserAccess
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.helper import get_user_by_role


class ProjectFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = Project

    name = factory.Faker("name")
    type_ = factory.Iterator(["VA", "HA"])
    creator_id = None

    @classmethod
    async def async_prep(cls, session: AsyncSession, kwargs: dict):
        """Fetch Admin user and inject as creator_id if not provided."""
        if "creator_id" not in kwargs or kwargs["creator_id"] is None:
            admin = await get_user_by_role(session, "Admin")
            if admin is None:
                raise RuntimeError("Admin user does not exist in test DB.")
            kwargs["creator_id"] = admin.id
        return kwargs


class EnvironmentFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = Environment

    name = factory.Faker("name")
    project = factory.SubFactory(ProjectFactory)


class ProductFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = Product

    name = factory.Faker("name")
    environment = factory.SubFactory(EnvironmentFactory)


class ProductUserAccessFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = ProductUserAccess

    user_id = factory.Faker("uuid4")
    product_id = factory.Faker("uuid4")
    granted = True
