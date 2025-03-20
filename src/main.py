from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.application.utils import startup_db
from src.routes import router

app = FastAPI(title="Sentinel", on_startup=[startup_db])

app.mount("/assets", StaticFiles(directory="public/assets"), name="assets")

app.include_router(router)
