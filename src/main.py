from contextlib import asynccontextmanager
from logging import Logger
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.application.utils import scheduler, startup_db
from src.presentation.html.exception_handler import exception_handlers
from src.routes import router
from prometheus_fastapi_instrumentator import Instrumentator

from .config import settings


logger = Logger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_db()

    scheduler.scheduler.start()
    await scheduler.scheduler_tasks()
    for job in scheduler.scheduler.get_jobs():
        logger.info(f"JOB -> {job}")

    if settings.ENABLE_PROMOTHEUS:
        global instrumentor
        logger.info("Promotheus monitoring setting up...")
        instrumentor.expose(app)
        logger.info("Promotheus monitoring ready")

    yield
    logger.info("Cleaning before shutdown!")
    scheduler.scheduler.shutdown()


app = FastAPI(
    title="Sentinel",
    exception_handlers=exception_handlers,
    lifespan=lifespan,
)

instrumentor = Instrumentator().instrument(app)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="public/assets"), name="assets")

app.include_router(router)
