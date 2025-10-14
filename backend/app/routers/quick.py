# backend/app/routers/quick.py
from __future__ import annotations

import os
import re
import json
import unicodedata
import difflib
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
# Stopwords & tokenization
# =========================
BASE_STOPWORDS = {
    "i","me","my","myself","we","our","ours","ourselves","you","your","yours","yourself","yourselves",
    "he","him","his","himself","she","her","hers","herself","it","its","itself","they","them","their",
    "theirs","themselves","what","which","who","whom","this","that","these","those","am","is","are",
    "was","were","be","been","being","have","has","had","having","do","does","did","doing","a","an",
    "the","and","but","if","or","because","as","until","while","of","at","by","for","with","about",
    "against","between","into","through","during","before","after","above","below","to","from","up",
    "down","in","out","on","off","over","under","again","further","then","once","here","there","when",
    "where","why","how","all","any","both","each","few","more","most","other","some","such","no",
    "nor","not","only","own","same","so","than","too","very","s","t","can","will","just","don","should",
    "now","also","via"
}

JOB_POST_STOPWORDS = {
    "role","position","job","team","department","organization","company","employer","employee","candidate","candidates",
    "applicant","applicants","application","applications","apply","applying","hiring","recruit","recruiting","recruitment",
    "responsibility","responsibilities","requirement","requirements","qualification","qualifications","preferred",
    "preference","skills","experience","experiences","background","overview","summary","description","about","benefits",
    "perk","perks","salary","compensation","range","hourly","deadline","guideline","guidelines","consideration",
    "considered","consider","eligible","eligibility","opportunity","opportunities","equal","visa","sponsorship",
    "remote","onsite","hybrid","full-time","fulltime","part-time","parttime","contract","internship","volunteer",
    "available","availability","schedule","scheduling","shift","shifts","hours","hour","day","days","week","weeks","month","months","year","years",
    "include","including","includes","inclusive","must","should","would","could","may","might","plus","etc",
    "materials","documents","document","documentation","submit","submission","submissions","process","processes","procedures",
    "preferred qualifications","preferred skills","nice to have","you will","you’ll","you will be","you are","we are","we’re",
    "mission","values","culture","teamwork","collaboration","collaborate","work","working","workload","workflows",
    "environment","office","offices","in-office","in office","on-site","on site","onboard","onboarding","train","training"
}

DATE_TIME_STOPWORDS = {
    "monday","tuesday","wednesday","thursday","friday","saturday","sunday",
    "mon","tue","tues","wed","thu","thur","thurs","fri","sat","sun",
    "january","february","march","april","may","june","july","august","september","october","november","december",
    "jan","feb","mar","apr","jun","jul","aug","sep","sept","oct","nov","dec",
    "am","pm","cst","est","pst","mst","utc","gmt","ct","pt","et","mt",
    "today","tomorrow","yesterday"
}

PLATFORM_FLUFF_STOPWORDS = {
    "social","media","platform","platforms","content","contents","online","digital","internet","web","website",
    "trends","trend","audience","audiences","community","communities"
}

_STOPWORDS = BASE_STOPWORDS | JOB_POST_STOPWORDS | DATE_TIME_STOPWORDS | PLATFORM_FLUFF_STOPWORDS

_ALPHA_TOKEN = re.compile(r"[A-Za-z][A-Za-z.+#-]{2,}")
_TIMEY = re.compile(r"^\d{1,2}(:?\d{2})?(am|pm)?$", re.IGNORECASE)
_NUMERICISH = re.compile(r"^[\d$.,%-]+$")

def _singularize(tok: str) -> str:
    if len(tok) <= 3:
        return tok
    if tok.endswith("ies") and len(tok) > 4:
        return tok[:-3] + "y"
    if tok.endswith(("sses","shes","ches")):
        return tok[:-2]
    if tok.endswith("es") and len(tok) > 4:
        return tok[:-2]
    if tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok

def _tokset(text: str) -> set[str]:
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

# =========================
# JD extraction & scoring
# =========================
_SECTION_HDRS = [
    "qualifications","preferred qualifications","preferred skills",
    "it is expected","responsibilities","requirements","what you'll do","what you will do",
    "about you","about the role","skills","must have","nice to have","you have","you will"
]
_HEADER_LINE = re.compile(r"^\s*[A-Z][A-Za-z0-9 &/’'()-]{2,}:\s*$")
_BULLET = re.compile(r"^\s*[-*•]\s+(.*)$", re.IGNORECASE)

def _clean_phrase(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[()•·–—]", " ", s)
    s = re.sub(r"[:;.,]+$", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = s.lower()
    words = [w for w in re.findall(r"[a-zA-Z][a-zA-Z+#.-]*", s) if w not in _STOPWORDS]
    if not words:
        return ""
    if len(words) == 1 and words[0] in _STOPWORDS:
        return ""
    return " ".join(words)

def _split_phrases(line: str) -> list[str]:
    parts = re.split(r",|;| and | or ", (line or "").strip(), flags=re.IGNORECASE)
    out: list[str] = []
    for p in parts:
        ph = _clean_phrase(p)
        if ph and 1 <= len(ph.split()) <= 6:
            out.append(ph)
    return out

def _extract_required_phrases(job_text: str) -> list[str]:
    lines = (job_text or "").splitlines()
    phrases: list[str] = []
    in_section = False

    def add_line(ln: str):
        for ph in _split_phrases(ln):
            phrases.append(ph)

    for ln in lines:
        raw = ln.strip()
        low = raw.lower()

        # Start a known section?
        if any(h in low for h in _SECTION_HDRS) or _HEADER_LINE.match(raw):
            in_section = True
            continue

        # End of a section?
        if in_section and (raw == "" or _HEADER_LINE.match(raw) or any(h in low for h in _SECTION_HDRS)):
            in_section = any(h in low for h in _SECTION_HDRS) or bool(_HEADER_LINE.match(raw))
            continue

        if in_section:
            m = _BULLET.match(ln)
            if m:
                add_line(m.group(1))
            else:
                add_line(raw)

    # Fallback: any bullets anywhere
    if not phrases:
        for ln in lines:
            m = _BULLET.match(ln)
            if m:
                add_line(m.group(1))

    # Dedupe, preserve order
    seen, out = set(), []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out

def _resume_token_sets(resume_text: str) -> tuple[set[str], set[str]]:
    toks = [t for t in re.findall(r"[a-zA-Z][a-zA-Z+#.-]*", (resume_text or "").lower())
            if t not in _STOPWORDS and len(t) >= 2 and not any(ch.isdigit() for ch in t)]
    unigrams = set(_singularize(t) for t in toks)
    bigrams = set()
    for a, b in zip(toks, toks[1:]):
        a, b = _singularize(a), _singularize(b)
        if a in _STOPWORDS or b in _STOPWORDS:
            continue
        bigrams.add(f"{a} {b}")
    return unigrams, bigrams

def _covered(phrase: str, uni: set[str], bi: set[str]) -> bool:
    words = phrase.split()
    if len(words) >= 2 and phrase in bi:
        return True
    return all(_singularize(w) in uni for w in words)

def _score_and_missing_from_required(resume_text: str, job_text: str, cap: int = 12) -> tuple[int, list[str], list[str]]:
    reqs = _extract_required_phrases(job_text)
    uni, bi = _resume_token_sets(resume_text)
    if not reqs:
        return 0, [], []
    used, missing = [], []
    for p in reqs:
        (used if _covered(p, uni, bi) else missing).append(p)
    score = int(round(100 * len(used) / max(1, len(reqs))))
    return max(0, min(100, score)), missing[:cap], used
def _score_and_missing_hybrid(resume_text: str, job_text: str, cap: int = 12) -> tuple[int, list[str], list[str]]:
    """
    Hybrid scorer:
      1) If we can extract requirement phrases from the JD, score coverage vs those phrases.
      2) Otherwise, fall back to full-text token overlap with your filtered tokenizer.
    Returns: (score%, missing_items, present_items)
    """
    # Try requirement phrase coverage first
    reqs = _extract_required_phrases(job_text)
    if reqs:
        uni, bi = _resume_token_sets(resume_text)
        used, missing = [], []
        for p in reqs:
            (used if _covered(p, uni, bi) else missing).append(p)
        score = int(round(100 * len(used) / max(1, len(reqs))))
        return max(0, min(100, score)), missing[:cap], used

    # Fallback: full-text token overlap (robust when JD is free-form or only a title)
    R = _tokset(resume_text)
    J = _tokset(job_text)
    if not J:
        return 0, [], []
    overlap = sorted(R & J)
    missing = sorted(J - R)[:cap]
    score = int(round(100 * len(overlap) / max(1, len(J))))
    return max(0, min(100, score)), missing, overlap

# =========================
# Models
# =========================
class QuickTailorRequest(BaseModel):
    resume_text: str
    job_text: str
    user_tweaks: Dict[str, Any] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

class BetterCandidateRequest(BaseModel):
    resume_text: str
    job_text: str

# =========================
# Helpers
# =========================
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

def _heuristic_changes(before: str, after: str, cap: int = 6) -> list[str]:
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

# ---- Better-candidate (on-demand LLM) ----
def _coerce_actions_json(text: str) -> list[dict]:
    if not text:
        return []
    s = text.strip()
    m = re.search(r"```json\s*(\{.*?}|\[.*?])\s*```", s, flags=re.DOTALL | re.IGNORECASE)
    if m:
        s = m.group(1).strip()
    try:
        obj = json.loads(s)
        if isinstance(obj, list):
            out = []
            for it in obj:
                if isinstance(it, dict):
                    title = (it.get("title") or "").strip()
                    why = (it.get("why") or "").strip()
                    steps = it.get("steps") or []
                    if title:
                        out.append({"title": title, "why": why, "steps": steps if isinstance(steps, list) else []})
            return out
    except Exception:
        pass
    lines = [ln.strip("-• ").strip() for ln in s.splitlines() if ln.strip()]
    out = []
    for ln in lines[:5]:
        out.append({"title": ln, "why": "", "steps": []})
    return out

def call_llm_better_candidate(resume_text: str, job_text: str) -> list[dict]:
    if not _client or not OPENAI_API_KEY:
        return []
    system = (
        "You are a career coach. Analyze the job description and resume to identify gaps. "
        "Generate 5 specific, actionable tasks:\n\n"
        "IMMEDIATE (timeframe='now') - 3 tasks doable TODAY (1-4 hours each):\n"
        "- Create/write a TANGIBLE work sample using existing skills (e.g., write sample SOP, edit existing doc, create process diagram)\n"
        "- Draft/prepare a SPECIFIC deliverable mentioned in the job (e.g., user guide, technical spec, workflow doc)\n"
        "- Quantify or improve an existing achievement from their resume\n"
        "AVOID: Generic advice like 'research company' or 'update LinkedIn'\n\n"
        "LONGER-TERM (timeframe='later') - 2 tasks for skill-building (1-4 weeks):\n"
        "- Learn SPECIFIC missing tool/skill from job requirements\n"
        "- Build portfolio project demonstrating key requirement\n\n"
        "Output valid JSON ONLY: [{\"title\":\"Create a sample SOP for...\",\"timeframe\":\"now\"}, ...]"
    )
    user = f"JOB DESCRIPTION:\n{job_text}\n\nRESUME (verbatim):\n{resume_text}\n"
    raw = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=700,
        temperature=0.3,
    ) or ""
    return _coerce_actions_json(raw)

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
# Actions (heuristic fallback)
# =========================
def _actions_from_missing(missing: list[str], job_text: str = "") -> tuple[list[str], list[str]]:
    jt = (job_text or "").lower()
    is_admissions = (("admission" in jt or "admissions" in jt) and ("application" in jt or "evaluate" in jt or "reader" in jt))
    is_video = ("video" in jt or "videograph" in jt or "producer" in jt or "premiere" in jt or "after effects" in jt)

    top = [w for w in missing if len(w.split()) >= 1][:3]
    joined = ", ".join(top) if top else "key criteria"

    if is_video:
        do_now = [
            "Assemble a 60–90s vertical reel from existing footage; add captions, simple motion titles, and music; export in 9:16 and 16:9.",
            "Shoot a 30–60s piece at a local event; stabilize, color-correct, mix levels, and add SRT captions.",
            "Create two alt cuts of the same story (fast vs. slow pacing) to show range; deliver platform-appropriate hooks.",
        ]
        do_long = [
            "Build a mini style guide: fonts, lower-thirds, captions, color pipeline, export presets (YouTube/IG/TikTok).",
            "Produce a 2–3 min feature: storyboard → shoot → edit → grade → mix → captions → thumbnail; track KPIs.",
        ]
    elif is_admissions:
        do_now = [
            "Complete a quick FERPA refresher and write a 5-bullet checklist for confidential handling.",
            "Practice 3 narrative summaries (120–180 words) using a template: context → academics → activities → contribution potential.",
            "Draft a one-page rubric for curriculum rigor, academic performance, extracurricular impact, and community fit; test on one file.",
        ]
        do_long = [
            "Run a timed reading sprint of 10 sample files (20–25 minutes each). Track pace/quality, iterate the rubric once.",
            "Create a 3–4 page reader handbook with exemplar narratives, common patterns, and edge cases.",
        ]
    else:
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

    # Score against extracted required phrases
    score, missing, used = _score_and_missing_hybrid(resume_text, job_text)
    
    # Use AI to generate job-specific action items
    ai_actions = call_llm_better_candidate(resume_text, job_text)
    
    # Extract do_now and do_long from AI response based on timeframe
    if ai_actions and len(ai_actions) > 0:
        do_now = []
        do_long = []
        
        for action in ai_actions:
            if isinstance(action, dict):
                title = action.get('title', '')
                timeframe = action.get('timeframe', 'now').lower()
                
                if timeframe == 'now':
                    do_now.append(title)
                else:
                    do_long.append(title)
        
        # If parsing failed or empty, use fallback
        if not do_now and not do_long:
            # Try splitting by position (first 3 = now, rest = later)
            for action in ai_actions[:3]:
                if isinstance(action, dict):
                    do_now.append(action.get('title', ''))
            for action in ai_actions[3:]:
                if isinstance(action, dict):
                    do_long.append(action.get('title', ''))
    else:
        # Fallback to heuristic if AI fails
        do_now, do_long = _actions_from_missing(missing, job_text=job_text)

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
            "present_keywords": used,
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

@router.post("/better-candidate")
def better_candidate(req: BetterCandidateRequest):
    resume_text = _nfkc(req.resume_text or "")
    job_text = _nfkc(req.job_text or "")
    if not resume_text or not job_text:
        raise HTTPException(status_code=400, detail="Both resume_text and job_text are required.")
    actions = call_llm_better_candidate(resume_text, job_text)
    if not actions:
        return {"llm_ok": False, "actions": []}
    return {"llm_ok": True, "actions": actions}

# =========================
# Career Analytics Endpoint
# =========================
class AnalyticsRequest(BaseModel):
    resume_text: str

@router.post("/career-analytics")
def career_analytics(req: AnalyticsRequest):
    """
    Analyze a resume and return YouTube-style career analytics using AI
    """
    resume_text = req.resume_text or ""
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required")
    
    if not _client:
        raise HTTPException(status_code=500, detail="OpenAI client not available")
    
    try:
        # AI prompt to generate personalized analytics
        prompt = f"""You are a career analytics engine designed for Gen Z and Gen Alpha job seekers. Analyze this resume and provide insights like YouTube Studio provides to creators.

Resume:
{resume_text}

Return a JSON object with the following structure (be adaptive to whatever field/industry this resume represents):

{{
  "creative_focus": {{"Industry 1": percentage, "Industry 2": percentage, ...}},
  "core_strength_zones": ["Strength 1", "Strength 2", ...],
  "experience_depth_years": estimated_years_of_experience,
  "skill_stack_health": {{"Core": percentage, "Growth": percentage, "Emerging": percentage}},
  "momentum_indicators": ["Momentum signal 1", "Momentum signal 2", ...],
  "recommended_focus_next": ["Action 1", "Action 2", "Action 3"],
  "adjacent_opportunities": [
    {{"skill_combo": "Skill A + Skill B", "opportunity": "Role/field they could pivot to"}},
    {{"skill_combo": "Skill C + Skill D", "opportunity": "Another adjacent role/field"}}
  ],
  "potential_new_skills": ["Skill suggestion 1", "Skill suggestion 2", ...],
  "ai_skills_to_explore": ["AI skill 1", "AI skill 2", ...],
  "extracted_skills": ["Skill 1", "Skill 2", ...]
}}

Guidelines:
- **creative_focus**: Identify 2-4 industries/fields they work in with percentage breakdown (must sum to 100)
- **core_strength_zones**: List 3-5 core competencies based on their experience
- **experience_depth_years**: Estimate total years of professional experience (integer)
- **skill_stack_health**: Categorize their skills into Core (fundamental to their field), Growth (advancing skills), and Emerging (new/learning) with percentages (must sum to 100)
- **momentum_indicators**: 2-4 positive growth signals or trends in their career
- **recommended_focus_next**: 3-4 actionable next steps to advance their career
- **adjacent_opportunities**: 3-5 strategic, future-proof career pivots based on their top skill combinations. This is NOT about "changing majors" or random job suggestions—it's about identifying SMART pivots that leverage their existing skills in ways that are tech-resilient and high-value. Show them "What ELSE can I do that positions me well for the future?" Focus on:
  - Roles that emphasize HUMAN skills (creativity, judgment, relationships, strategy, taste, empathy) that technology can't easily replicate
  - Fields where their expertise becomes MORE valuable as tech evolves (e.g., someone needs to guide, curate, validate, design for humans)
  - Opportunities that are growing, not shrinking—but don't make everything about "AI" or "tech"
  Format: {{"skill_combo": "Skill X + Skill Y", "opportunity": "Specific role or field (brief why it's future-proof)"}}. Examples:
  - Writer: {{"skill_combo": "Storytelling + Research", "opportunity": "Brand Strategist (companies need authentic narratives, not just content)"}}
  - Barista: {{"skill_combo": "Customer Service + Multitasking", "opportunity": "Client Success Manager (relationships and judgment can't be automated)"}}
  - Nurse: {{"skill_combo": "Patient Care + Critical Thinking", "opportunity": "Care Coordinator or Patient Advocate (empathy and complex decision-making)"}}
  - Developer: {{"skill_combo": "Problem Solving + Communication", "opportunity": "Solutions Architect or Technical Consultant (bridging human needs and tech)"}}
  - Teacher: {{"skill_combo": "Mentorship + Curriculum Design", "opportunity": "Learning Experience Designer (personalized education needs human insight)"}}
  Be specific, strategic, and empowering. Frame pivots as SMART career moves that leverage their HUMAN strengths in a tech-evolving world. Don't make every suggestion AI-related—focus on roles where human judgment, creativity, relationships, and taste are the core value.
- **potential_new_skills**: 4-6 relevant skills they should learn based on their field (non-AI)
- **ai_skills_to_explore**: 4-6 cutting-edge, LATEST AI tools/skills that would benefit their specific career path. Be specific about HOW they'd use it in their actual work. Focus on tools that are actively trending and widely adopted RIGHT NOW. Examples by field:
  - Creative: "Claude/ChatGPT for scriptwriting", "Runway for video generation", "ElevenLabs for voice", "Midjourney/DALL-E for visuals"
  - Tech: "Cursor/GitHub Copilot for coding", "v0/Bolt for rapid prototyping", "AI code review tools"
  - Business: "Perplexity for deep research", "Notion AI for docs", "ChatGPT for strategy/analysis"
  - Healthcare: "AI medical scribing", "Diagnostic support AI"
  - Retail/Service: "AI customer service bots", "Predictive inventory AI"
  - Design: "Figma AI", "Framer AI", "Relume for web design"
  Only suggest tools that are CURRENTLY available and being used by professionals. Be practical and actionable. Avoid anything outdated or deprecated.
- **extracted_skills**: List 8-12 specific skills mentioned in their resume

Be encouraging, specific, and adaptive to ANY career field (tech, retail, healthcare, creative, trades, etc.).
Prioritize the MOST CURRENT and WIDELY-ADOPTED AI tools available right now.
Return ONLY valid JSON, no markdown or extra text."""

        # Call OpenAI
        if _new_api:
            response = _client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            analytics_json = response.choices[0].message.content.strip()
        else:
            response = _client.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            analytics_json = response['choices'][0]['message']['content'].strip()
        
        # Parse JSON response
        # Remove markdown code blocks if present
        analytics_json = analytics_json.replace("```json", "").replace("```", "").strip()
        analytics = json.loads(analytics_json)
        
        return analytics
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")
