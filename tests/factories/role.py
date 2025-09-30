import factory

from src.domain.entity import Role


class RoleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Role
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("email")
    super_admin = False
    required_project_access = True
