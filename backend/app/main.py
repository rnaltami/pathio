# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env BEFORE importing routers so quick.py sees the env vars
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from .routers.public import router as public_router
from .routers.quick import router as quick_router

app = FastAPI(title="Pathio Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_router)
app.include_router(quick_router, prefix="")
