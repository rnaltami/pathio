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
# --- begin replacement /export handler in backend/app/main.py ---

# -----------------------------
# OVERRIDE /export with résumé-specific cleanup
# - Summary moved to top as real heading
# - one blank line after Summary
# - "What changed" removed
# - all markdown (** _ ` etc.) stripped from paragraphs
# -----------------------------
from fastapi import APIRouter
from pydantic import BaseModel
import re

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
    return s

def _remove_what_changed(md: str) -> str:
    """
    Remove the 'What changed' section (any of '**What changed**' or '# What changed', case-insensitive)
    and everything after it.
    """
    m = re.search(r'(?im)^\s*(?:\*\*\s*what\s+changed\s*\*\*|#{1,6}\s*what\s+changed)\b.*$', md, re.M)
    if not m:
        return md
    return md[:m.start()].rstrip()

def _extract_summary(md: str) -> tuple[str | None, str]:
    """
    Return (summary_block_markdown, rest_without_summary).
    Captures from the '**Summary**' (or '# Summary') header line through lines up to
    (but not including) the next section header-like line:
      - markdown heading:    # / ## / ### ...
      - bold header line:    **Section**
    Works whether the summary is bullets or a paragraph.
    """
    if not md:
        return None, md
    lines = md.splitlines()

    # locate summary header (bold or markdown heading)
    start = None
    for i, line in enumerate(lines):
        if re.fullmatch(r'\s*(\*\*\s*summary\s*\*\*|#{1,6}\s*summary)\s*', line.strip(), flags=re.IGNORECASE):
            start = i
            break
    if start is None:
        return None, md

    def is_header_like(s: str) -> bool:
        s = s.strip()
        if not s:
            return False
        if s.startswith("#"):
            return True
        if re.fullmatch(r"\*\*.+\*\*", s):   # bold-only header line
            return True
        return False

    end = start + 1
    while end < len(lines):
        if is_header_like(lines[end]):
            break
        end += 1

    summary_block = "\n".join(lines[start:end]).strip()
    rest = ("\n".join(lines[:start] + lines[end:])).strip()
    return summary_block, rest

@export_router.post("/export")
def export_doc(req: ExportRequest):
    # Choose content
    content = req.tailored_resume_md if req.which == "resume" else req.cover_letter_md
    if not content:
        return Response(
            content=b"No content to export.",
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="export.txt"'},
            status_code=400,
        )

    # Résumé-specific layout: Summary (clean) at top, blank line, then body; drop What changed
    if req.which == "resume":
        md = _remove_what_changed(content)
        summary_block, body_without_summary = _extract_summary(md)

        if summary_block:
            # Drop the header line itself and keep bullets/paragraph that follow
            summary_lines = summary_block.splitlines()
            summary_body = "\n".join(summary_lines[1:]).strip()
            # Build a clean markdown doc: H1 Summary + body (we'll strip inline md later)
            clean_top = "# Summary\n"
            if summary_body:
                clean_top += summary_body + "\n"
            clean_top += "\n"  # blank line after summary
            content = (clean_top + (body_without_summary or "")).strip()
        else:
            content = md  # No summary present; still without 'What changed'

    # Try to build DOCX; fallback to stripped text
    try:
        from docx import Document  # python-docx
    except Exception:
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

        # Headings
        if line.startswith("# "):
            doc.add_heading(_strip_markdown_inline(line[2:].strip()), level=1)
            continue
        if line.startswith("## "):
            doc.add_heading(_strip_markdown_inline(line[3:].strip()), level=2)
            continue
        if line.startswith("### "):
            doc.add_heading(_strip_markdown_inline(line[4:].strip()), level=3)
            continue

        # Horizontal rules / separators
        if re.fullmatch(r"\s*-{3,}\s*", line):
            doc.add_paragraph("")
            continue

        # Bullets
        m = bullet_pattern.match(line)
        if m:
            text = _strip_markdown_inline(m.group(1).strip())
            try:
                doc.add_paragraph(text, style="List Bullet")
            except Exception:
                doc.add_paragraph("• " + text)
            continue

        # Blank line
        if not line.strip():
            doc.add_paragraph("")
            continue

        # Normal paragraph
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

# Mount last so it overrides any earlier /export
app.include_router(export_router)
