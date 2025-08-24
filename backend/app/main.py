# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Routers
# If you have these files, keep both imports; if you only use quick.py, you can comment public_router.
from .routers.quick import router as quick_router
try:
    from .routers.public import router as public_router
except Exception:
    public_router = None  # safe if public.py doesn't exist / is unused

app = FastAPI()

# --- CORS (allow your frontend to call the API) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # later: restrict to your Streamlit domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include routers ---
app.include_router(quick_router)
if public_router:
    app.include_router(public_router)

# --- Health check (what Render/you will hit) ---
@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})

# --- (Optional) Friendly root page ---
@app.get("/")
def root():
    return {
        "service": "Pathio backend",
        "status": "ok",
        "routes": ["/quick-tailor", "/export", "/coach", "/healthz"]
    }
