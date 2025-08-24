import tempfile, os
from .models import ResumeJSON
from typing import List

async def parse_resume(file) -> ResumeJSON:
    suffix = os.path.splitext(file.filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        path = tmp.name

    text = ""
    if suffix == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            pass
    if not text and suffix in (".docx", ".doc"):
        try:
            import docx2txt
            text = docx2txt.process(path) or ""
        except Exception:
            pass
    if not text:
        raise ValueError("Could not extract text from file")

    os.unlink(path)

    # basic heuristics
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    skills: List[str] = []
    for i, l in enumerate(lines):
        if l.lower().startswith("skills"):
            skills = [s.strip() for s in l[len("skills"):].split(",") if s.strip()]
            break

    return ResumeJSON(
        name=lines[0] if lines else None,
        email=next((l for l in lines if "@" in l and "." in l), None),
        phone=next((l for l in lines if any(c.isdigit() for c in l) and ("+" in l or "-" in l)), None),
        linkedin=next((l for l in lines if "linkedin.com" in l.lower()), None),
        summary=None,
        skills=skills,
        experience=[],
        education=[],
        raw_text=text,
    )
