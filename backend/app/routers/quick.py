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

# ---------- Keyword filtering for Insights ----------
# ---------- Keyword filtering for Insights (improved) ----------
_STOPWORDS = {
    # common function words
    "the","and","or","but","if","then","than","so","because","while","where","when",
    "for","with","from","into","over","under","between","within","without","about","above","below","after",
    "before","during","across","along","alongside","around","another",
    "to","in","on","at","by","of","as","per","via","per",
    "a","an","is","are","be","been","being","was","were","do","does","did","done","doing",
    "have","has","had","having","can","could","may","might","must","should","would","will",
    "this","that","these","those","such","same","other","each","every","any","all","some","most","more","many","few",
    "it","its","itself","they","them","their","theirs","we","our","ours","you","your","yours","i","me","my","mine",
    # job-post fluff / boilerplate
    "position","role","team","department","responsibilities","requirements","preferred","qualifications","preference",
    "materials","process","summary","including","include","includes","including",
    "work","working","hours","availability","schedule","scheduling","remote","onsite","entirely",
    "training","onboarding","week","weeks","day","days","month","months","year","years",
    "applicant","applicants","candidates","candidate","staff","office","mission","values",
    # edu context
    "college","university","liberal","arts","education",
    # timezones / time words
    "am","pm","cst","est","pst","mst","utc","monday","tuesday","wednesday","thursday","friday","saturday","sunday",
}

_ALPHA_TOKEN = re.compile(r"[A-Za-z][A-Za-z.+#-]{2,}")  # keep letters; allow + . # -
_TIMEY = re.compile(r"^\d{1,2}(:?\d{2})?(am|pm)?$", re.IGNORECASE)  # 9, 9am, 9:00, 9:00pm
_NUMERICISH = re.compile(r"^[\d$.,%-]+$")  # money, percents, pure numbers

def _singularize(tok: str) -> str:
    """Ultra-light singularization to align 'admissions'~'admission', 'studies'~'study'."""
    if len(tok) <= 3: 
        return tok
    if tok.endswith("ies") and len(tok) > 4:
        return tok[:-3] + "y"
    if tok.endswith("sses") or tok.endswith("shes") or tok.endswith("ches"):
        return tok[:-2]  # classes->class (keep 'ss'), matches->match
    if tok.endswith("es") and len(tok) > 4:
        return tok[:-2]
    if tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok

def _tokset(text: str) -> set[str]:
    """
    Extract a deduped set of meaningful tokens:
      - alphabetic (letters, may include + . # - inside)
      - lowercased, lightly singularized
      - length >= 3
      - exclude stopwords and numeric/time-like tokens
    """
    out: set[str] = set()
    if not text:
        return out
    s = (text or "").lower()
    for raw in _ALPHA_TOKEN.findall(s):
        tok = raw.strip(".+#-")
        if len(tok) < 3:
            continue
        if _TIMEY.match(tok) or _NUMERICISH.match(tok):
            continue
        if any(ch.isdigit() for ch in tok):
            continue
        if tok in _STOPWORDS:
            continue
        tok = _singularize(tok)
        if tok in _STOPWORDS or len(tok) < 3:
            continue
        out.add(tok)
    return out

def _match_and_missing(resume_text: str, job_text: str, cap: int = 12) -> tuple[int, list[str]]:
    """
    Simple overlap score + top missing keywords from the job using filtered tokens.
    """
    R = _tokset(resume_text)
    J = _tokset(job_text)
    if not J:
        return 0, []

    overlap = len(R & J)
    score = int(round(100 * overlap / max(1, len(J))))
    missing = sorted(J - R)[:cap]  # deterministic & readable

    return max(0, min(100, score)), missing


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
import difflib

def _heuristic_changes(before: str, after: str, cap: int = 6) -> list[str]:
    """
    Compute a simple line-based diff between before and after resumes.
    Returns up to `cap` bullet strings like 'Removed X', 'Added Y'.
    """
    before_lines = [ln.strip() for ln in before.splitlines() if ln.strip()]
    after_lines = [ln.strip() for ln in after.splitlines() if ln.strip()]
    diff = list(difflib.ndiff(before_lines, after_lines))
    changes = []
    for d in diff:
        if d.startswith("- "):
            changes.append(f"Removed: {d[2:]}")
        elif d.startswith("+ "):
            changes.append(f"Added: {d[2:]}")
        if len(changes) >= cap:
            break
    return changes

def _nfkc(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).replace("\u00A0", " ")
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    return s.strip()

def _chat(messages: List[Dict[str, str]], max_tokens: int = 1600, temperature: float = 0.35) -> Optional[str]:
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

# ---------- Insights (safe, non-fabricating) ----------
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+#-]{1,}")

def _tokset(text: str) -> set[str]:
    """
    Extract a deduped set of meaningful tokens:
    - alphabetic (letters, may include + . # - inside)
    - length >= 3
    - exclude stopwords
    - exclude numeric/time-like tokens (e.g., 9am, 20.40, 14-28)
    """
    out: set[str] = set()
    if not text:
        return out

    # normalize
    s = (text or "").lower()

    # find candidate tokens
    for raw in _ALPHA_TOKEN.findall(s):
        tok = raw.strip(".+#-")  # trim punctuation-ish suffix/prefix
        if len(tok) < 3:
            continue
        if _TIMEY.match(tok) or _NUMERICISH.match(tok):
            continue
        if any(ch.isdigit() for ch in tok):
            continue
        if tok in _STOPWORDS:
            continue
        out.add(tok)
    return out


def _match_and_missing(resume_text: str, job_text: str, cap: int = 12) -> tuple[int, list[str]]:
    """
    Compute a simple overlap score + top missing keywords from the job.
    Only considers filtered tokens (see _tokset).
    """
    R = _tokset(resume_text)
    J = _tokset(job_text)
    if not J:
        return 0, []

    overlap = len(R & J)
    score = int(round(100 * overlap / max(1, len(J))))
    # rank missing by a simple heuristic: alphabetical but you could later plug TF weights
    missing = sorted(J - R)[:cap]

    # clamp 0..100
    return max(0, min(100, score)), missing


def _actions_from_missing(missing: list[str], job_text: str = "") -> tuple[list[str], list[str]]:
    """
    Generate concrete 'do now' and 'do long' actions.
    If the role looks like admissions/application reading, use domain-tailored tasks.
    Otherwise, fall back to neutral actions referencing top missing keywords.
    """
    # Detect admissions/application-reader context
    jt = (job_text or "").lower()
    is_admissions = (
        ("admission" in jt or "admissions" in jt) and
        ("application" in jt or "evaluate" in jt or "reader" in jt)
    )

    top = [w for w in missing if len(w) >= 3][:3]
    joined = ", ".join(top) if top else "key requirements"

    if is_admissions:
        do_now = [
            "Skim 3–5 sample applications and practice writing 120–180-word narrative summaries using a consistent structure (context → academics → activities → contribution potential).",
            "Draft a one-page rubric for evaluating curriculum rigor, academic performance, extracurricular impact, and community contribution; test it on one sample.",
            "Set up a secure, organized workspace (folders, naming) and log template to ensure confidential handling and timely completion.",
        ]
        do_long = [
            "Build a 3–4 page 'reader handbook' for yourself: common patterns, red flags, and exemplar narratives tailored to selective liberal arts contexts.",
            "Complete a self-paced practice sprint: 10 timed reads (20–25 min each), track pace and accuracy, and iterate your rubric once.",
        ]
    else:
        # neutral fallback referencing actual missing keywords
        do_now = [
            f"Draft a 1-page alignment sheet mapping your bullets to {joined}. (time ~1–2h)",
            "Create a small, truthful sample artifact (checklist/outline/process doc) based on your current experience. (time ~3–4h)",
            "Write a short impact recap (before/after, scope, timing) from a past project. (time ~2–3h)",
        ]
        do_long = [
            "Turn one artifact into a portfolio piece with a clear README and trade-offs. (time ~1–2 wks)",
            "Iterate a workflow you already use and document the improvement. (time ~1–2 wks)",
        ]
    return do_now, do_long


# =========================
# Tailoring (STRICT)
# =========================
def call_llm_tailor(resume_text: str, job_text: str) -> Tuple[str, str, str]:
    """
    STRICT mode: Returns (tailored_resume_md, cover_letter_md, what_changed_md)
    or ('','','') if the LLM fails. No heuristic résumé fabrication.
    """
    if not _client or not OPENAI_API_KEY:
        return "", "", ""

    system = (
    "You are an expert resume editor.\n"
    "- REWRITE ONLY WHAT EXISTS in the source resume; do not invent tools, metrics, or achievements.\n"
    "- Keep it factual, concise, and ATS-friendly.\n"
    "- Use Markdown. No code fences.\n"
    "- When listing 'What changed', refer to specific bullets/sections that were modified, added, or removed.\n"
    "- Example: 'Condensed 3 script coordinator bullets into 2 clearer lines' or 'Removed unrelated casting director details'.\n"
    )

    # IMPORTANT: force a Summary header at the very top (grounded, ≤3 lines)
    user = (
        f"JOB DESCRIPTION:\n{job_text}\n\n"
        f"RESUME (verbatim source):\n{resume_text}\n\n"
        "TASKS:\n"
        "1) Rewrite the resume aligned to the job WITHOUT adding tools/skills/metrics not in the source.\n"
        "2) Start the tailored resume with a '**Summary**' header followed by 1–3 lines derived ONLY from the source resume.\n"
        "3) Draft a short cover letter (≤180 words) that stays factual to the source resume.\n"
        "4) Provide a short 'What changed' section (3–6 bullets) describing edits you made to align the resume.\n\n"
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
    llm_ok = bool(tailored_md and cover_md)
   
    if not what_changed_md and llm_ok:
    # fallback: generate concrete changes via diff
     changes = _heuristic_changes(resume_text, tailored_md)
     what_changed_md = "\n".join(f"- {c}" for c in changes)

    # Safe, non-fabricating insights (always computed)
    score, missing = _match_and_missing(resume_text, job_text)
    do_now, do_long = _actions_from_missing(missing, job_text=job_text)

    # Return a consistent payload whether LLM worked or not
    return {
        "tailored_resume_md": tailored_md if llm_ok else "",
        "cover_letter_md": cover_md if llm_ok else "",
        "what_changed_md": (what_changed_md or "") if llm_ok else "",
        "llm_ok": llm_ok,
        "error": None if llm_ok else "llm_unavailable",
        "insights": {
            "engine": "llm+heuristic" if llm_ok else "heuristic-only",
            "match_score": score,
            "missing_keywords": missing,
            "ats_flags": ["none"],
            "do_now": do_now,
            "do_long": do_long,
        },
    }


@router.post("/coach")
def coach(req: ChatRequest):
    msgs = req.messages or []
    system = "You are a practical, concise how-to coach. Respond with focused, step-by-step instructions."
    raw = _chat([{"role": "system", "content": system}] + msgs, max_tokens=700, temperature=0.2) or ""
    return {"reply": raw.strip() or "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"}
