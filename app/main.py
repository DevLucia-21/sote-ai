from fastapi import FastAPI
from app.api import stt

app = FastAPI(title="Sote AI API")

app.include_router(stt.router)
