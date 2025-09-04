# backend/app/routers/quick.py
from __future__ import annotations

import os
import re
import json
import unicodedata
from typing import List, Dict, Any, Tuple, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# =========================
# OpenAI client (new/old)
# =========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

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
# Helpers (tokenization / scoring)
# =========================
_WORD = re.compile(r"[A-Za-z][A-Za-z\-\./&+']+")
STOPWORDS = {
    "the","and","of","to","in","for","with","on","at","a","an","is","are","be","as",
    "by","from","or","that","this","it","we","you","your","their","our","they","but",
    "not","will","can","may","have","has","had","do","does","did","into","over","per"
}

def _nfkc(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).replace("\u00A0", " ")
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    return s.strip()

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

def match_and_missing(resume_text: str, job_text: str) -> Tuple[int, List[str]]:
    job = set(key_terms(job_text, limit=60))
    res = set(key_terms(resume_text, limit=200))
    if not job:
        return 0, []
    overlap = len(job & res)
    score = int(round(100.0 * overlap / max(1, len(job))))
    missing = sorted(job - res)
    return max(0, min(100, score)), missing

STOP_SAFE = set("a an the and or to for of with in on at by from as is be are was were it this that these those you your we our i me my".split())

def _tokset(text: str) -> set[str]:
    text = _nfkc(text).lower()
    toks = re.findall(r"[a-z0-9][a-z0-9.+#-]{1,}", text)
    return {t for t in toks if t not in STOP_SAFE}

def deterministic_match_score(resume_text: str, job_text: str) -> int:
    R, J = _tokset(resume_text), _tokset(job_text)
    if not R or not J:
        return 0
    overlap = len(R & J)
    score = int(round(100 * overlap / len(J)))
    if overlap > 0 and score == 0:
        score = 1
    return max(0, min(100, score))

# ---------- ATS checks (deterministic; safe to include) ----------
def ats_checks(resume_text: str) -> List[str]:
    flags: List[str] = []

    if len(resume_text) > 40000:
        flags.append("Resume is very long; consider trimming.")

    allowed = set("•–—“”‘’…·°®™©")
    raw = [c for c in resume_text if ord(c) > 127 and c not in allowed]
    total = max(1, len(resume_text))
    density = len(raw) / total

    if density >= 0.0025 and len(raw) >= 5:
        flags.append("Resume contains unusual non-ASCII characters; export as UTF-8.")
    else:
        if any(ord(c) > 127 for c in resume_text):
            flags.append("Curly quotes/bullets/dashes detected (OK). Ensure final export is UTF-8 or PDF.")

    if len(re.findall(r"\b[A-Z]{3,}\b", resume_text)) > 80:
        flags.append("Many ALL-CAPS tokens; reduce for ATS readability.")

    return flags or ["none"]

# =========================
# LLM helpers
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

def _extract_json(raw: str) -> Optional[dict]:
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start:end+1])
        except Exception:
            return None
    return None

# =========================
# LLM insights (strict)
# =========================
def llm_insight_score_miss(resume_text: str, job_text: str) -> Tuple[Optional[int], Optional[List[str]], str]:
    """Return (score, missing_skills, engine='llm') or (None, None, 'llm') on failure."""
    sys = (
        "You are a precise hiring copilot. Extract only missing skill-like keywords: tools, frameworks, metrics, "
        "workflows, certifications. Avoid filler ('and', 'must'), HR words, or locations."
    )
    user = (
        "Return strict JSON only:\n"
        "{\"score\": <0-100>, \"missing\": [string, string, ... up to 10]}\n\n"
        f"JOB:\n{job_text}\n\nRESUME:\n{resume_text}\n\n"
        "Rules:\n"
        "- 'missing' must be domain/skill terms (e.g., OBS, Airflow, CTR, run-of-show, talent pipeline).\n"
        "- Do not include generic words like 'any', 'role', 'skills', 'including', or locations.\n"
    )
    raw = _chat([{"role":"system","content":sys},{"role":"user","content":user}], max_tokens=300, temperature=0.0)
    data = _extract_json(raw or "")
    if not data:
        return None, None, "llm"

    s_raw = data.get("score", None)
    s: Optional[int] = None
    if s_raw is not None:
        try:
            if isinstance(s_raw, str):
                m = re.search(r"\d{1,3}", s_raw)
                if m:
                    s = int(m.group(0))
            elif isinstance(s_raw, (int, float)):
                s = int(round(float(s_raw)))
        except Exception:
            s = None

    missing = [str(x).strip() for x in (data.get("missing") or []) if isinstance(x, (str,int))]
    cleaned: List[str] = []
    seen = set()
    for m in missing:
        m = re.sub(r"\s+", " ", str(m)).strip(" .,-").strip()
        low = m.lower()
        if not m or low in {"any","role","skills","including"}:
            continue
        if low in seen:
            continue
        seen.add(low)
        cleaned.append(m)

    if s is None:
        return None, None, "llm"
    return max(0, min(100, s)), cleaned[:10], "llm"

# =========================
# Content sanitizer (prevent adding tools/metrics not in source)
# =========================
def _sentences(md: str) -> List[str]:
    parts: List[str] = []
    for line in (md or "").splitlines():
        if not line.strip():
            parts.append(line)
            continue
        if line.strip().startswith(("#", "-", "•", "*")):
            parts.append(line)
            continue
        segs = re.split(r'(?<=[.!?])\s+(?=[A-Z])', line)
        parts.extend(segs)
    return parts

def _normalize_tokens_set(text: str) -> set[str]:
    toks = re.findall(r"[a-z0-9][a-z0-9.+#-]{1,}", unicodedata.normalize("NFKC", (text or "").lower()))
    return set(toks)

_PROTECTED_CLUSTERS = [
    {"machine", "learning", "ml", "model", "models", "tensorflow", "pytorch", "spark", "hadoop", "mllib", "sagemaker"},
    {"a/b", "ab", "experimentation", "experiment", "ab-testing", "a-b"},
    {"statistical", "regression", "classification", "roc-auc", "ndcg", "map", "f1"},
    {"data-driven", "analytics"},
]

def sanitize_tailored(tailored_md: str, resume_text: str) -> str:
    src_tokens = _normalize_tokens_set(resume_text)
    has_percent_in_src = "%" in (resume_text or "")

    def allowed(sentence: str) -> bool:
        s = sentence.strip()
        if not s:
            return True
        low = unicodedata.normalize("NFKC", s.lower())

        if "%" in s and not has_percent_in_src:
            return False

        for cluster in _PROTECTED_CLUSTERS:
            if any(term in low for term in cluster):
                if not any(term in src_tokens for term in cluster):
                    return False
        return True

    lines = _sentences(tailored_md or "")
    kept = [ln for ln in lines if allowed(ln)]

    out: List[str] = []
    prev_blank = False
    for ln in kept:
        if not ln.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(ln)
    return "\n".join(out).strip()

# =========================
# Tailoring with STRICT fail (no fallbacks for docs)
# =========================
def call_llm_tailor(resume_text: str, job_text: str) -> Tuple[str, str]:
    """Return (tailored_resume_md, cover_letter_md) or ('','') if the LLM fails."""
    if not _client or not OPENAI_API_KEY:
        return "", ""

    system = (
        "You are an expert resume editor.\n"
        "- REWRITE ONLY WHAT EXISTS. Do not invent responsibilities, metrics, tools, or results.\n"
        "- If the job asks for skills the resume does not show, DO NOT claim them. Emphasize transferable skills instead.\n"
        "- Keep it factual, concise, ATS-friendly. Prefer neutral verbs over marketing language.\n"
        "- Use Markdown. Do not include code fences."
    )
    user_resume = (
        f"JOB DESCRIPTION:\n{job_text}\n\n"
        f"RESUME (verbatim source):\n{resume_text}\n\n"
        "TASKS:\n"
        "1) Rewrite the resume to align with the job WITHOUT adding new tools/skills/metrics not in the source.\n"
        "2) Draft a short cover letter (≤180 words) that stays factual to the source resume. Do not claim missing skills.\n"
        "Return as exactly two sections labeled:\n"
        "===TAILORED_RESUME===\n...\n===COVER_LETTER===\n...\n"
    )
    try:
        raw = _chat(
            [{"role":"system","content":system},{"role":"user","content":user_resume}],
            max_tokens=1400, temperature=0.35
        )
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
    except Exception:
        return "", ""

# =========================
# Routes
# =========================
@router.post("/quick-tailor")
def quick_tailor(req: QuickTailorRequest):
    # Normalize inputs to stabilize scoring & ATS heuristics
    resume_text = _nfkc(req.resume_text or "")
    job_text = _nfkc(req.job_text or "")
    if not resume_text or not job_text:
        raise HTTPException(status_code=400, detail="Both resume_text and job_text are required.")

    # STRICT: Get tailored docs from LLM; if missing, fail hard
    tailored_md, cover_md = call_llm_tailor(resume_text, job_text)
    if not tailored_md or not cover_md:
        raise HTTPException(
            status_code=503,
            detail="Tailoring is temporarily unavailable. Please try again in a moment."
        )

    # STRICT: Insights from LLM; if missing, fail hard
    score, missing, engine = llm_insight_score_miss(resume_text, job_text)
    if score is None or missing is None:
        raise HTTPException(
            status_code=503,
            detail="Tailoring is temporarily unavailable. Please try again in a moment."
        )

    # Actions from LLM; if missing, fail hard
    do_now, do_long = llm_actions(resume_text, job_text, missing or [])
    if do_now is None or do_long is None:
        raise HTTPException(
            status_code=503,
            detail="Tailoring is temporarily unavailable. Please try again in a moment."
        )

    return {
        "tailored_resume_md": tailored_md,
        "cover_letter_md": cover_md,
        "insights": {
            "engine": engine,  # "llm"
            "match_score": score,
            "missing_keywords": missing or [],
            "ats_flags": ats_checks(resume_text),
            "do_now": do_now,
            "do_long": do_long,
        },
    }

@router.post("/coach")
def coach(req: ChatRequest):
    """Lightweight how-to chat for the 'Show me how' link."""
    msgs = req.messages or []
    system = (
        "You are a practical, concise how-to coach. Answer with a focused step-by-step recipe "
        "for the user's request: list concrete steps, tools/menus/commands, and a small checklist. "
        "Avoid generic self-help advice; be specific and actionable."
    )
    chat = [{"role":"system","content":system}] + msgs
    raw = _chat(chat, max_tokens=700, temperature=0.2) or ""
    return {"reply": raw.strip() or "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"}
