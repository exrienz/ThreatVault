from sqlalchemy import URL, create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings

async_db_conn = URL.create(
    drivername=settings.ASYNC_DB_DRIVER, database=str(settings.DB_URL)
)

async_db_conn = f"{settings.ASYNC_DB_DRIVER}://{settings.DB_URL}"
sync_db_conn = f"{settings.SYNC_DB_DRIVER}://{settings.DB_URL}"

async_engine = create_async_engine(async_db_conn, echo=True)
sync_engine = create_engine(sync_db_conn)

AsyncSessionFactory = async_sessionmaker(bind=async_engine)
SyncSessionFactory = sessionmaker(bind=sync_engine)
