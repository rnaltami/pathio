# backend/app/routers/quick.py
from __future__ import annotations

import os
import re
import json
import unicodedata
from typing import List, Dict, Any, Tuple, Optional

from fastapi import APIRouter, HTTPException
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
    from openai import OpenAI  # >=1.x client
    if OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY)
        _new_api = True
except Exception:
    pass

if _client is None and OPENAI_API_KEY:
    try:
        import openai  # legacy client
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
# Helpers
# =========================
def _nfkc(s: str) -> str:
    """Normalize to NFKC, strip zero-width + NBSP, and trim."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).replace("\u00A0", " ")
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    return s.strip()

def _chat(
    messages: List[Dict[str, str]],
    max_tokens: int = 1600,
    temperature: float = 0.35,
) -> Optional[str]:
    """Unified chat call; returns content text or None on failure."""
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

def call_llm_tailor(resume_text: str, job_text: str) -> Tuple[str, str, str]:
    """
    STRICT mode: Returns (tailored_resume_md, cover_letter_md, what_changed_md)
    or ('','','') if the LLM fails. No heuristic fabrication.
    """
    if not _client or not OPENAI_API_KEY:
        return "", "", ""

    system = (
        "You are an expert resume editor.\n"
        "- REWRITE ONLY WHAT EXISTS in the source resume; do not invent tools, metrics, or achievements.\n"
        "- Keep it factual, concise, ATS-friendly.\n"
        "- Use Markdown. No code fences.\n"
    )
    user = (
        f"JOB DESCRIPTION:\n{job_text}\n\n"
        f"RESUME (verbatim source):\n{resume_text}\n\n"
        "TASKS:\n"
        "1) Rewrite the resume aligned to the job WITHOUT adding tools/skills/metrics not present in the source.\n"
        "2) Draft a short cover letter (≤180 words) that stays factual to the source resume.\n"
        "3) Provide a short 'What changed' section (3–6 bullets) describing the edits you made to align the resume.\n\n"
        "Return exactly three sections in this order:\n"
        "===TAILORED_RESUME===\n...\n"
        "===COVER_LETTER===\n...\n"
        "===WHAT_CHANGED===\n- bullet 1\n- bullet 2\n- ...\n"
    )

    raw = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=1600,
        temperature=0.35,
    )
    if not raw:
        return "", "", ""

    tail, cover, changed = "", "", ""
    if "===TAILORED_RESUME===" in raw:
        _, rest = raw.split("===TAILORED_RESUME===", 1)
        if "===COVER_LETTER===" in rest:
            tail, rest2 = rest.split("===COVER_LETTER===", 1)
            if "===WHAT_CHANGED===" in rest2:
                cover, changed = rest2.split("===WHAT_CHANGED===", 1)
            else:
                cover = rest2
        else:
            tail = rest
    else:
        # Very defensive fallback parse (still strict; no fabrication)
        parts = raw.split("**Cover", 1)
        tail = parts[0].strip()
        cover = ("**Cover" + parts[1]).strip() if len(parts) > 1 else ""

    return tail.strip(), cover.strip(), changed.strip()

# =========================
# Routes
# =========================
@router.post("/quick-tailor")
def quick_tailor(req: QuickTailorRequest):
    resume_text = _nfkc(req.resume_text or "")
    job_text = _nfkc(req.job_text or "")
    if not resume_text or not job_text:
        raise HTTPException(status_code=400, detail="Both resume_text and job_text are required.")

    tailored_md, cover_md, what_changed_md = call_llm_tailor(resume_text, job_text)
    if not tailored_md or not cover_md:
        # Surface a clean, friendly error for the frontend (no silent fabrication)
        return JSONResponse(
            status_code=503,
            content={"error": "Tailoring service temporarily unavailable. Please try again in a minute."},
        )

    return {
        "tailored_resume_md": tailored_md,
        "cover_letter_md": cover_md,
        "what_changed_md": what_changed_md or "",
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
    system = "You are a practical, concise how-to coach. Respond with focused, step-by-step instructions."
    raw = _chat([{"role": "system", "content": system}] + msgs, max_tokens=700, temperature=0.2) or ""
    return {
        "reply": raw.strip() or "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"
    }
