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

def _normalize(s: str) -> str:
    return (s or "").replace("\u00A0", " ").strip()

def _is_header_line(line: str, name: str) -> bool:
    """True if line looks like a header with 'name' (case-insensitive), ignoring *, _, # wrappers."""
    raw = _normalize(line)
    # remove leading header/formatting marks
    raw = re.sub(r"^[#*\s_>-\.:]+", "", raw)
    raw = re.sub(r"[*_#\s]+$", "", raw)
    return raw.lower() == name.lower()

def _remove_summary_block(md: str) -> str:
    """Remove a '**Summary**' header + its immediate paragraph/bullets."""
    if not md:
        return ""
    lines = md.splitlines()
    out = []
    i = 0
    while i < len(lines):
        if _is_header_line(lines[i], "summary"):
            i += 1
            # skip blank lines
            while i < len(lines) and not lines[i].strip():
                i += 1
            # consume bullets/paragraph until a blank line OR new header-like line
            while i < len(lines):
                ln = lines[i]
                if not ln.strip():
                    i += 1
                    break
                # stop if next header-like marker
                if re.match(r"^\s*(#+\s+|[*_]{0,3}[A-Za-z].*\*\*?$)", ln):
                    # allow content but if it looks like a next section header (e.g. "**Experience**")
                    # detect by heavy emphasis at both ends or hash headings
                    hdrish = bool(re.match(r"^\s*#+\s+\S", ln)) or bool(re.match(r"^\s*[*_]{1,3}[^*].*[*_]{1,3}\s*$", ln))
                    if hdrish:
                        break
                i += 1
            # fall through: do NOT append summary part
            continue
        out.append(lines[i])
        i += 1
    # clean extra blank lines
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt

def _remove_what_changed(md: str) -> str:
    """Remove '**What changed**' section entirely (from header to end)."""
    if not md:
        return ""
    lines = md.splitlines()
    for idx, ln in enumerate(lines):
        if _is_header_line(ln, "what changed"):
            return "\n".join(lines[:idx]).rstrip()
    return md

def _strip_markdown_inline(text: str) -> str:
    """Remove markdown marks, including unbalanced cases."""
    if not text:
        return ""
    s = text

    # links: [text](url) -> text (url)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)

    # bold/italics/code (balanced)
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"__(.*?)__", r"\1", s)
    s = re.sub(r"\*(.*?)\*", r"\1", s)
    s = re.sub(r"_(.*?)_", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)

    # strip leftover emphasis characters around edges (unbalanced cases like *Heading**)
    s = re.sub(r"(^|\s)[*_]{1,3}(\S)", r"\1\2", s)  # leading *, **, _
    s = re.sub(r"(\S)[*_]{1,3}(\s|$)", r"\1\2", s)  # trailing *, **, _

    # collapse multiple spaces produced by stripping
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def _preprocess_for_resume(md: str) -> str:
    """For résumé export: drop Summary + What changed, then strip inline markdown."""
    if not md:
        return ""
    md2 = _remove_summary_block(md)
    md3 = _remove_what_changed(md2)
    # strip inline marks on each line
    cleaned = "\n".join(_strip_markdown_inline(ln) for ln in md3.splitlines())
    # remove lone horizontal rules / extra dashes
    cleaned = re.sub(r"(?m)^\s*-{3,}\s*$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

def _preprocess_for_cover(md: str) -> str:
    """For cover letter export: keep content, just strip inline markdown."""
    if not md:
        return ""
    cleaned = "\n".join(_strip_markdown_inline(ln) for ln in md.splitlines())
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

@export_router.post("/export")
def export_doc(req: ExportRequest):
    if req.which == "resume":
        content = _preprocess_for_resume(req.tailored_resume_md or "")
    else:
        content = _preprocess_for_cover(req.cover_letter_md or "")

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
        # Fallback to .txt
        return Response(
            content=content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="export.txt"'},
        )

    doc = Document()
    bullet_re = re.compile(r"^\s*[-*•]\s+(.*)$")

    for raw in content.splitlines():
        line = raw.rstrip("\n")

        # simple headings heuristic: lines in ALL CAPS or lines ending with ':' get a heading style
        if re.match(r"^[A-Z0-9 ,/&()'’.-]{6,}$", line) and line.strip() == line.upper():
            doc.add_heading(line.strip(), level=2)
            continue
        if line.strip().endswith(":") and len(line.strip()) <= 48:
            doc.add_heading(line.strip().rstrip(":"), level=2)
            continue

        m = bullet_re.match(line)
        if m:
            text = m.group(1).strip()
            try:
                doc.add_paragraph(text, style="List Bullet")
            except Exception:
                doc.add_paragraph("• " + text)
            continue

        if not line.strip():
            doc.add_paragraph("")
            continue

        doc.add_paragraph(line)

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
