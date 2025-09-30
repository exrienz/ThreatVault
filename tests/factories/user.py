import factory

from src.application.security.oauth2.password import pwd_context
from src.domain.entity import User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    email = factory.Faker("email")
    username = factory.Faker("name")
    password = pwd_context.hash("Password@123")
    active = True
    login_via_email = True
    role_id = factory.Faker("role_id")
