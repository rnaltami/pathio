# backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Routers
from .routers.quick import router as quick_router
try:
    from .routers.public import router as public_router
except Exception:
    public_router = None  # safe if public.py doesn't exist / is unused

app = FastAPI(title="Pathio Backend")

# -----------------------------
# CORS (Frontend(s) allowed)
# -----------------------------
# You can override with env: ALLOWED_ORIGINS="https://your-frontend.onrender.com,https://pathio.streamlit.app"
_env_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

# Defaults: keep Streamlit for rollback, allow your new Render frontend domain, and local dev.
# If you know your exact Render URL, add it here (e.g., "https://pathio-frontend.onrender.com").
default_origins = [
    "https://pathio.streamlit.app",  # existing Streamlit frontend (rollback)
    "http://localhost:8501",         # local Streamlit dev
]

# Use env-specified origins if provided; otherwise fall back to defaults.
allow_origins = _env_origins or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    # Allow any *.onrender.com frontend (safer than "*" but flexible if you rename the service)
    allow_origin_regex=r"^https://[a-zA-Z0-9-]+\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Routers
# -----------------------------
app.include_router(quick_router)
if public_router:
    app.include_router(public_router)

# -----------------------------
# Health & Root
# -----------------------------
@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})

@app.get("/")
def root():
    return {
        "service": "Pathio backend",
        "status": "ok",
        "routes": ["/quick-tailor", "/export", "/coach", "/healthz"],
        "cors_allowed": allow_origins,
    }
