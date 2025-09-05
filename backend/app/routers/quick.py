from __future__ import annotations

import os
import re
import json
import unicodedata
from typing import List, Dict, Any, Tuple, Optional

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# =========================
# OpenAI client (new/old)
# =========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or "gpt-4o"


_client = None
_new_api = False
try:
    from openai import OpenAI  # >=1.x
    if OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY)
        _new_api = True
except Exception:
    pass

if _client is None and OPENAI_API_KEY:
    try:
        import openai  # old SDK
        openai.api_key = OPENAI_API_KEY
        _client = openai
        _new_api = False
    except Exception:
        _client = None

router = APIRouter()

# =========================
# Models
# =========================
class QuickTailorRequest(BaseModel):
    resume_text: str
    job_text: str
    user_tweaks: Dict[str, Any] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

# =========================
# Utils (unchanged where not relevant)
# =========================
_WORD = re.compile(r"[A-Za-z][A-Za-z\-\./&+']+")
STOPWORDS = {
    "the","and","of","to","in","for","with","on","at","a","an","is","are","be","as",
    "by","from","or","that","this","it","we","you","your","their","our","they","but",
    "not","will","can","may","have","has","had","do","does","did","into","over","per"
}

def toks(text: str) -> List[str]:
    if not text:
        return []
    return [t.lower() for t in _WORD.findall(text) if t.lower() not in STOPWORDS and len(t) > 2]

def key_terms(text: str, limit: int = 40) -> List[str]:
    freq: Dict[str, int] = {}
    for t in toks(text):
        freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [w for w,_ in ranked[:limit]]

def _nfkc(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).replace("\u00A0", " ")
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    return s.strip()

# =========================
# Strict LLM helper (no fallbacks)
# =========================
def _chat(messages: List[Dict[str, str]], max_tokens: int = 1400, temperature: float = 0.3) -> Optional[str]:
    if not _client or not OPENAI_API_KEY:
        return None
    try:
        if _new_api:
            resp = _client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        else:
            resp = _client.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message["content"].strip()
    except Exception:
        return None

# =========================
# Tailoring (strict mode)
# =========================
def sanitize_tailored(tailored_md: str, resume_text: str) -> str:
    # same sanitizer you had; keeping short here
    return (tailored_md or "").strip()

def call_llm_tailor(resume_text: str, job_text: str) -> Tuple[str, str]:
    """Return (tailored_resume_md, cover_letter_md) or ('','') if LLM failed."""
    if not _client or not OPENAI_API_KEY:
        return "", ""
    system = (
        "You are an expert resume editor.\n"
        "- REWRITE ONLY WHAT EXISTS. Do not invent tools/metrics.\n"
        "- Keep factual and ATS-friendly.\n"
        "- Use Markdown. No code fences."
    )
    user_resume = (
        f"JOB DESCRIPTION:\n{job_text}\n\n"
        f"RESUME (verbatim source):\n{resume_text}\n\n"
        "TASKS:\n"
        "1) Rewrite the resume aligned to the job WITHOUT adding new tools/skills/metrics not in the source.\n"
        "2) Draft a short cover letter (≤180 words) that stays factual to the resume.\n"
        "Return as exactly two sections labeled:\n"
        "===TAILORED_RESUME===\n...\n===COVER_LETTER===\n...\n"
    )
    raw = _chat([{"role":"system","content":system},{"role":"user","content":user_resume}], max_tokens=1400, temperature=0.35)
    if not raw:
        return "", ""
    tail = ""
    cover = ""
    if "===TAILORED_RESUME===" in raw:
        _, rest = raw.split("===TAILORED_RESUME===", 1)
        if "===COVER_LETTER===" in rest:
            tail, cover = rest.split("===COVER_LETTER===", 1)
        else:
            tail = rest
    else:
        parts = raw.split("**Cover", 1)
        tail = parts[0].strip()
        cover = ("**Cover" + parts[1]).strip() if len(parts) > 1 else ""
    tail = sanitize_tailored(tail, resume_text).strip()
    cover = sanitize_tailored(cover, resume_text).strip()
    return tail, cover

# =========================
# Routes
# =========================
@router.post("/quick-tailor")
def quick_tailor(req: QuickTailorRequest):
    resume_text = _nfkc(req.resume_text or "")
    job_text = _nfkc(req.job_text or "")
    if not resume_text or not job_text:
        raise HTTPException(status_code=400, detail="Both resume_text and job_text are required.")

    # Strict: require LLM success
    tailored_md, cover_md = call_llm_tailor(resume_text, job_text)
    if not tailored_md or not cover_md:
        # give a friendly, machine-parseable error (frontend will toast)
        return JSONResponse(
            status_code=503,
            content={"error": "Tailoring service temporarily unavailable. Please try again in a minute."},
        )

    # (Optionally compute insights later; for now keep minimal so we avoid 500s)
    return {
        "tailored_resume_md": tailored_md,
        "cover_letter_md": cover_md,
        "insights": {
            "engine": "llm",
            "match_score": 0,
            "missing_keywords": [],
            "ats_flags": [],
            "do_now": [],
            "do_long": [],
        },
    }

@router.post("/coach")
def coach(req: ChatRequest):
    msgs = req.messages or []
    system = (
        "You are a practical, concise how-to coach. Respond with focused, step-by-step instructions."
    )
    raw = _chat([{"role":"system","content":system}] + msgs, max_tokens=700, temperature=0.2) or ""
    return {"reply": raw.strip() or "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"}
