# backend/app/main.py
import os
import re
from pathlib import Path

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# =========================
# .env early load (so quick.py gets env at import time)
# =========================
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)
except Exception:
    pass

app = FastAPI(title="Pathio Backend")

# =========================
# CORS
# =========================
_env_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
default_origins = [
    "https://pathio.streamlit.app",  # Streamlit fallback frontend
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

# =========================
# Clean /export router (REGISTERED FIRST)
# =========================
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
    raw = re.sub(r"^[#*\s_>-\.:]+", "", raw)
    raw = re.sub(r"[*_#\s]+$", "", raw)
    return raw.lower() == name.lower()

def _remove_summary_block(md: str) -> str:
    """Remove a 'Summary' header + its immediate paragraph/bullets."""
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
            # consume bullets/paragraph until blank OR clear next header-like line
            while i < len(lines):
                ln = lines[i]
                if not ln.strip():
                    i += 1
                    break
                # stop if the next line is clearly a section header
                hdrish = bool(re.match(r"^\s*#+\s+\S", ln)) or bool(re.match(r"^\s*[*_]{1,3}[^*].*[*_]{1,3}\s*$", ln))
                if hdrish:
                    break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt

def _remove_what_changed(md: str) -> str:
    """Remove 'What changed' section entirely (from its header to end)."""
    if not md:
        return ""
    lines = md.splitlines()
    for idx, ln in enumerate(lines):
        if _is_header_line(ln, "what changed"):
            return "\n".join(lines[:idx]).rstrip()
    return md

def _strip_markdown_inline(text: str) -> str:
    """Remove markdown marks (handles unbalanced cases like *Heading**)."""
    if not text:
        return ""
    s = text
    # links: [text](url) -> text (url)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)
    # balanced emphasis/code
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"__(.*?)__", r"\1", s)
    s = re.sub(r"\*(.*?)\*", r"\1", s)
    s = re.sub(r"_(.*?)_", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    # unbalanced cleanup
    s = re.sub(r"(^|\s)[*_]{1,3}(\S)", r"\1\2", s)  # leading
    s = re.sub(r"(\S)[*_]{1,3}(\s|$)", r"\1\2", s)  # trailing
    # collapse spaces
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def _preprocess_for_resume(md: str) -> str:
    """For résumé export: drop Summary + What changed, then strip inline markdown."""
    if not md:
        return ""
    md2 = _remove_summary_block(md)
    md3 = _remove_what_changed(md2)
    cleaned = "\n".join(_strip_markdown_inline(ln) for ln in md3.splitlines())
    cleaned = re.sub(r"(?m)^\s*-{3,}\s*$", "", cleaned)  # remove hr lines
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
            headers={
                "Content-Disposition": 'attachment; filename="export.txt"',
                "X-Exporter": "clean",
            },
            status_code=400,
        )

    # Try DOCX; fallback to TXT
    try:
        from docx import Document  # python-docx
    except Exception:
        return Response(
            content=content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="export.txt"',
                "X-Exporter": "clean",
            },
        )

    doc = Document()
    bullet_re = re.compile(r"^\s*[-*•]\s+(.*)$")

    for raw in content.splitlines():
        line = raw.rstrip("\n")

        # simple heading heuristics
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
        headers={
            "Content-Disposition": 'attachment; filename="pathio_export.docx"',
            "X-Exporter": "clean",
        },
    )

# Register the CLEAN export router FIRST so it takes precedence
app.include_router(export_router)

# =========================
# Other routers (after export)
# =========================
from .routers.quick import router as quick_router
try:
    from .routers.public import router as public_router
except Exception:
    public_router = None

app.include_router(quick_router)
if public_router:
    app.include_router(public_router)

# =========================
# Health & Root
# =========================
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
