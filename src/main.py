import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.application.exception.exception_handlers import GlobalExceptionHandler
from src.application.utils import scheduler, startup_db
from src.routes import router

from .config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_db()
    scheduler.scheduler.start()
    await scheduler.scheduler_tasks()
    for job in scheduler.scheduler.get_jobs():
        logger.info(f"Scheduled Job -> {job}")
    yield
    scheduler.scheduler.shutdown()


app = FastAPI(
    title="Sentinel",
    lifespan=lifespan,
)

exception_handler = GlobalExceptionHandler()


@app.exception_handler(HTTPException)
def general_exception_handler(request: Request, exc: HTTPException):
    return exception_handler(request, exc)


@app.exception_handler(Exception)
def general_exception_handler_(request: Request, exc: Exception):
    return exception_handler(request, exc)


app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="static"), name="assets")

app.include_router(router)
