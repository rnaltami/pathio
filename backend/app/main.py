# backend/app/main.py
import os
import re
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

# NEW: load .env very early, so quick.py sees env vars at import time
try:
    from dotenv import load_dotenv
    # .env is in backend/, and this file is backend/app/main.py
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)
except Exception:
    pass

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

default_origins = [
    "https://pathio.streamlit.app",  # existing Streamlit frontend (rollback)
    "http://localhost:8501",         # local Streamlit dev
]

allow_origins = _env_origins or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
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

# -----------------------------
# OVERRIDE /export here to clean Markdown when python-docx is available
# (If your project already defines /export inside routers.quick, you can
# either remove that version or keep only this one by naming it identically.)
# -----------------------------
from fastapi import APIRouter
from pydantic import BaseModel

export_router = APIRouter()

class ExportRequest(BaseModel):
    tailored_resume_md: str
    cover_letter_md: str
    which: str  # "resume" or "cover"

def _strip_markdown_inline(s: str) -> str:
    """Remove basic Markdown marks so DOCX doesn't show **, __, ``, etc."""
    if not s:
        return ""
    # links: [text](url) -> text (url)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)
    # bold/italics/code
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"__(.*?)__", r"\1", s)
    s = re.sub(r"\*(.*?)\*", r"\1", s)
    s = re.sub(r"_(.*?)_", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    # strip residual emphasis chars
    return s

@export_router.post("/export")
def export_doc(req: ExportRequest):
    content = req.tailored_resume_md if req.which == "resume" else req.cover_letter_md
    if not content:
        return Response(
            content=b"No content to export.",
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="export.txt"'},
            status_code=400,
        )

    try:
        from docx import Document  # python-docx
    except Exception:
        # Fallback: plain text with markdown stripped (so ** are gone even in .txt)
        txt = "\n".join(_strip_markdown_inline(line) for line in content.splitlines())
        return Response(
            content=txt.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="export.txt"'},
        )

    doc = Document()

    bullet_pattern = re.compile(r"^\s*[-*•]\s+(.*)$")
    for raw in content.splitlines():
        line = raw.rstrip("\n")
        # headings (support #, ##, ###)
        if line.startswith("# "):
            doc.add_heading(_strip_markdown_inline(line[2:].strip()), level=1)
            continue
        if line.startswith("## "):
            doc.add_heading(_strip_markdown_inline(line[3:].strip()), level=2)
            continue
        if line.startswith("### "):
            doc.add_heading(_strip_markdown_inline(line[4:].strip()), level=3)
            continue

        # horizontal rules or explicit separators
        if re.fullmatch(r"\s*-{3,}\s*", line):
            doc.add_paragraph("")  # add a small gap
            continue

        # bullet lists
        m = bullet_pattern.match(line)
        if m:
            text = _strip_markdown_inline(m.group(1).strip())
            try:
                p = doc.add_paragraph(text, style="List Bullet")
            except Exception:
                p = doc.add_paragraph("• " + text)
            continue

        # blank line -> paragraph gap
        if not line.strip():
            doc.add_paragraph("")
            continue

        # normal paragraph (markdown emphasis removed)
        doc.add_paragraph(_strip_markdown_inline(line))

    import io
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return Response(
        content=bio.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="pathio_export.docx"'},
    )

# Mount the export override last to ensure it wins
app.include_router(export_router)
