from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

oauth2_password_scheme = OAuth2PasswordBearer("/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
