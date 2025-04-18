from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.application.middlewares import RequestMiddleware
from src.application.utils import startup_db
from src.presentation.html.exception_handler import exception_handlers
from src.routes import router

# from fastapi.middleware.cors import CORSMiddleware

# from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(
    title="Sentinel", on_startup=[startup_db], exception_handlers=exception_handlers
)

app.add_middleware(RequestMiddleware)

app.mount("/assets", StaticFiles(directory="public/assets"), name="assets")

app.include_router(router)
