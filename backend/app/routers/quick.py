from __future__ import annotations

import os
import re
import json
import unicodedata
from typing import List, Dict, Tuple, Optional

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
    from openai import OpenAI  # SDK >= 1.x
    if OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY)
        _new_api = True
except Exception:
    pass

if _client is None and OPENAI_API_KEY:
    try:
        import openai  # legacy SDK
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
    user_tweaks: Dict[str, str] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

# =========================
# Utils
# =========================
_WORD = re.compile(r"[A-Za-z][A-Za-z\-\./&+']+")
STOPWORDS = {
    "the","and","of","to","in","for","with","on","at","a","an","is","are","be","as",
    "by","from","or","that","this","it","we","you","your","their","our","they","but",
    "not","will","can","may","have","has","had","do","does","did","into","over","per"
}

def _nfkc(s: str) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKC", s).replace("\u00A0", " ")
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    return s.strip()

def toks(text: str) -> List[str]:
    if not text: return []
    return [t.lower() for t in _WORD.findall(text) if t.lower() not in STOPWORDS and len(t) > 2]

def key_terms(text: str, limit: int = 40) -> List[str]:
    freq: Dict[str, int] = {}
    for t in toks(text):
        freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [w for w,_ in ranked[:limit]]

# token set used by deterministic score + filtering
def _tokset(text: str) -> set[str]:
    text = _nfkc(text).lower()
    return set(re.findall(r"[a-z0-9][a-z0-9.+#-]{1,}", text))

def deterministic_match_score(resume_text: str, job_text: str) -> int:
    R, J = _tokset(resume_text), _tokset(job_text)
    if not R or not J: return 0
    overlap = len(R & J)
    score = int(round(100 * overlap / max(1, len(J))))
    return max(0, min(100, score))

_GENERIC_BAN = {
    "ability","abilities","any","across","activities","adherence","administrative","analysis","assign","assigned",
    "assigning","assistants","attention","availability","based","basic","bundle","calendar","cheat","clips","coaching",
    "collect","competing","compile","compliance","coordinate","coordination","daily","data","ensure","execution","host",
    "hosts","live","livestream","manage","operational","organizational","performance","product","reporting","role","skills",
    "smooth","state","status","applicants","application","including","include","such","must","work","working","before","when"
}
def _is_skilllike(s: str) -> bool:
    s = (s or "").strip(" .,:;()[]").strip()
    if not s or len(s) < 2: return False
    low = s.lower()
    if low in _GENERIC_BAN: return False
    if " " in low: return True
    if re.search(r"(sql|airflow|scrapy|sagemaker|athena|glue|boto3|notion|jira|asana|tableau|looker|duckdb|spark|pytorch|tensorflow|vertex|bigquery|kafka|redis|elasticsearch|powerbi|ga4|ctr|ndcg|map@|f1|auc|obs)$", low):
        return True
    if re.search(r"[A-Z]{2,}", s):  # acronyms like CTR/KPI
        return True
    return False

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
# OpenAI wrapper
# =========================
def _chat(messages: List[Dict[str, str]], max_tokens: int = 1400, temperature: float = 0.3) -> Optional[str]:
    if not _client or not OPENAI_API_KEY:
        return None
    try:
        if _new_api:
            resp = _client.chat.completions.create(
                model=OPENAI_MODEL, messages=messages,
                temperature=temperature, max_tokens=max_tokens
            )
            return (resp.choices[0].message.content or "").strip()
        else:
            resp = _client.ChatCompletion.create(
                model=OPENAI_MODEL, messages=messages,
                temperature=temperature, max_tokens=max_tokens
            )
            return resp.choices[0].message["content"].strip()
    except Exception:
        return None

# =========================
# Tailoring (strict)
# =========================
def sanitize_tailored(tailored_md: str, resume_text: str) -> str:
    return (tailored_md or "").strip()

def call_llm_tailor(resume_text: str, job_text: str) -> Tuple[str, str]:
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
    raw = _chat(
        [{"role":"system","content":system},{"role":"user","content":user_resume}],
        max_tokens=1400, temperature=0.35
    )
    if not raw:
        return "", ""
    tail, cover = "", ""
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
    return sanitize_tailored(tail, resume_text).strip(), sanitize_tailored(cover, resume_text).strip()

# =========================
# Insights (robust)
# =========================
def llm_insight_score_miss(resume_text: str, job_text: str) -> Tuple[Optional[int], Optional[List[str]], str]:
    """
    Prefer LLM JSON (new SDK response_format), then legacy; finally return None to allow heuristic blend.
    Post-filters 'missing' to ensure truly absent + skill-like.
    """
    def _coerce_score(x) -> Optional[int]:
        try:
            if isinstance(x, str):
                m = re.search(r"\d+(?:\.\d+)?", x)
                if not m: return None
                x = float(m.group(0))
            else:
                x = float(x)
            if 0 <= x <= 1: x *= 100.0
            s = int(round(x))
            return max(0, min(100, s))
        except Exception:
            return None

    def _post(items: List[str]) -> List[str]:
        R = _tokset(resume_text)
        out, seen = [], set()
        for m in items or []:
            m = re.sub(r"\s+", " ", str(m)).strip(" .,-")
            if not m or not _is_skilllike(m): continue
            key = m.lower()
            if key in seen or key in R: continue
            seen.add(key); out.append(m)
            if len(out) >= 10: break
        return out

    system = "You are an impartial hiring copilot. Output ONLY strict JSON. No prose. No backticks."
    user = (
        'Return JSON exactly: {"score": <0-100>, "missing": ["skill","tool","metric",... up to 10]}\n'
        "Rules:\n"
        "- 'score' is JD↔resume fit (0–100).\n"
        "- 'missing' must be skill-like: tools, frameworks, metrics, workflows, certifications.\n"
        "- Exclude soft skills, locations, and generic words (role, skills, including, any, etc.).\n"
        "- Keep items short (1–3 words). No duplicates.\n\n"
        f"JOB DESCRIPTION:\n{job_text}\n\nRESUME:\n{resume_text}\n"
    )

    content: Optional[str] = None

    # Attempt 1: JSON-enforced (new SDK)
    if _client and OPENAI_API_KEY and _new_api:
        try:
            resp = _client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role":"system","content":system},{"role":"user","content":user}],
                temperature=0.0, max_tokens=300,
                response_format={"type":"json_object"},
            )
            content = (resp.choices[0].message.content or "").strip()
        except Exception:
            content = None

    # Attempt 2: generic (legacy or fallback)
    if not content and _client and OPENAI_API_KEY:
        try:
            raw = _chat(
                [{"role":"system","content":system},{"role":"user","content":user}],
                max_tokens=300, temperature=0.0
            )
            content = (raw or "").strip()
        except Exception:
            content = None

    # Attempt 3: ultra-terse retry
    if not content and _client and OPENAI_API_KEY:
        try:
            raw = _chat(
                [{"role":"system","content":'Return JSON only: {"score":int,"missing":[str,...]}'},
                 {"role":"user","content":f"JD:\n{job_text}\n\nRESUME:\n{resume_text}"}],
                max_tokens=200, temperature=0.0
            )
            content = (raw or "").strip()
        except Exception:
            content = None

    data = None
    if content:
        try:
            data = json.loads(content)
        except Exception:
            start, end = content.find("{"), content.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(content[start:end+1])
                except Exception:
                    data = None

    if not data:
        return None, None, "heuristic"

    score = _coerce_score(data.get("score"))
    missing = _post(list(data.get("missing") or []))

    # Stabilize score with deterministic blend
    if score is not None:
        try:
            det = deterministic_match_score(resume_text, job_text)
            score = int(round(0.65 * score + 0.35 * det))
            score = max(0, min(100, score))
        except Exception:
            pass

    return score, missing, "llm"

def match_and_missing(resume_text: str, job_text: str) -> Tuple[int, List[str]]:
    job = set(key_terms(job_text, limit=60))
    res = set(key_terms(resume_text, limit=200))
    overlap = len(job & res)
    score = int(round(100.0 * overlap / max(1, len(job))))
    # heuristic missing, filtered to skill-like
    missing = [w for w in sorted(job - res) if _is_skilllike(w)]
    return max(0, min(100, score)), missing

def build_actions_fallback(missing: List[str]) -> Tuple[List[str], List[str]]:
    safe_missing = [m for m in (missing or []) if isinstance(m, str)]
    focus = ", ".join(safe_missing[:3]) if safe_missing else "the role’s core tasks"
    do_now = [
        f"Create a one-page alignment sheet mapping your bullets to {focus}. (time: ~1–2 hours)",
        "Draft a sample work artifact (process doc / outline / checklist) using tools already on your résumé. (time: ~3–4 hours)",
        "Compile a simple impact sheet from past projects (before/after, volume, quality, timing). (time: ~2–3 hours)",
    ]
    do_long = [
        "Turn the artifact into a small portfolio repo with a README and trade-off notes. (time: ~1–2 weeks)",
        "Improve a workflow/template you already use and document the change. (time: ~1–2 weeks)",
    ]
    return do_now[:3], do_long[:2]

def llm_actions(resume_text: str, job_text: str, missing_skills: List[str]) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    sys = "You design concrete, measurable upskilling actions for candidates. Output JSON only."
    user = (
        '{ "do_now": [string, string, string], "do_long": [string, string] }\n'
        "Constraints:\n"
        "- Each 'do_now' is hands-on and yields an artifact (repo/notebook/report/dashboard/demo/case study).\n"
        "- Be specific: tools, datasets, metrics. < 230 chars each. Include time estimate.\n"
        "- 'do_long' may include at most one course/cert; otherwise deeper project/OSS.\n\n"
        f"JOB:\n{job_text}\n\nRESUME:\n{resume_text}\n\nMISSING SKILLS: {missing_skills}\n"
    )
    raw = _chat([{"role":"system","content":sys},{"role":"user","content":user}], max_tokens=500, temperature=0.2)
    if not raw: return None, None
    try:
        data = json.loads(raw.strip().strip("`"))
    except Exception:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(raw[start:end+1])
            except Exception:
                return None, None
        else:
            return None, None

    do_now = [str(x).strip() for x in (data.get("do_now") or []) if isinstance(x, (str,int))]
    do_long = [str(x).strip() for x in (data.get("do_long") or []) if isinstance(x, (str,int))]

    def _clean(items: List[str], is_now: bool) -> List[str]:
        out: List[str] = []
        for s in items:
            s = re.sub(r"\s+", " ", s)
            if len(s) < 12: continue
            if not re.search(r"(repo|notebook|readme|report|dashboard|demo|case study|artifact|portfolio|gist|PR|evaluation)", s, re.I):
                if not is_now and re.search(r"(course|certification|specialization|certificate)", s, re.I):
                    pass
                else:
                    continue
            if not re.search(r"\b(\d+[-\s]?(hour|day|week)s?)\b", s, re.I):
                s += " (time: ~4–6 hours)" if is_now else " (time: ~1–3 weeks)"
            out.append(s[:230])
        if not is_now:
            kept, course_used = [], False
            for it in out:
                if re.search(r"(course|certification|specialization|certificate)", it, re.I):
                    if course_used: continue
                    course_used = True
                kept.append(it)
            return kept[:2]
        return out[:3]

    return _clean(do_now, True), _clean(do_long, False)

# =========================
# Routes
# =========================
@router.post("/quick-tailor")
def quick_tailor(req: QuickTailorRequest):
    resume_text = _nfkc(req.resume_text or "")
    job_text = _nfkc(req.job_text or "")

    if not resume_text or not job_text:
        raise HTTPException(status_code=400, detail="Both resume_text and job_text are required.")

    # Strict tailoring: require LLM success
    tailored_md, cover_md = call_llm_tailor(resume_text, job_text)
    if not tailored_md or not cover_md:
        return JSONResponse(
            status_code=503,
            content={"error": "Tailoring service temporarily unavailable. Please try again in a minute."},
        )

    # Insights: LLM + deterministic blend, safe fallbacks (no fabrication)
    score, missing, engine = llm_insight_score_miss(resume_text, job_text)
    h_score, h_missing = match_and_missing(resume_text, job_text)

    if score is None:
        score, engine = h_score, "heuristic"
    else:
        # if LLM is zero but heuristic finds signal, bump to heuristic
        if score == 0 and h_score > 0:
            score, engine = h_score, "heuristic"

    if not missing:
        missing = h_missing

    flags = ats_checks(resume_text)

    # Actions: prefer LLM; fallback to generic—but never fabricate résumé content
    try:
        do_now, do_long = llm_actions(resume_text, job_text, missing or [])
        if not do_now or not do_long:
            raise ValueError("Empty LLM actions")
    except Exception:
        do_now, do_long = build_actions_fallback(missing or [])

    return {
        "tailored_resume_md": tailored_md,
        "cover_letter_md": cover_md,
        "insights": {
            "engine": engine,
            "match_score": int(score or 0),
            "missing_keywords": missing or [],
            "ats_flags": flags,
            "do_now": do_now or [],
            "do_long": do_long or [],
        },
    }

@router.post("/coach")
def coach(req: ChatRequest):
    msgs = req.messages or []
    system = "You are a practical, concise how-to coach. Respond with focused, step-by-step instructions."
    raw = _chat([{"role":"system","content":system}] + msgs, max_tokens=700, temperature=0.2) or ""
    return {"reply": raw.strip() or "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"}
