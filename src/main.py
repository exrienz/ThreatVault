from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.application.utils import scheduler, startup_db
from src.presentation.html.exception_handler import exception_handlers
from src.routes import router

from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_db()
    scheduler.scheduler.start()
    await scheduler.scheduler_tasks()
    for job in scheduler.scheduler.get_jobs():
        print(job)
    yield
    scheduler.scheduler.shutdown()


app = FastAPI(
    title="Sentinel",
    exception_handlers=exception_handlers,
    lifespan=lifespan,
)

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
