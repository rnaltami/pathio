# backend/app/insights.py
from .models import ResumeJSON, JobPostingJSON
from typing import List

ATS_BANNED = ["table", "image", "header", "footer", "text box"]

def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    # very simple tokenizer: alpha words, lowercased
    return [w.lower() for w in text.split() if w.isalpha()]

async def compute_insights(resume: ResumeJSON, job: JobPostingJSON):
    r_words = set(_tokenize(resume.raw_text or ""))
    j_words = set(_tokenize(job.raw_text or ""))

    # naive overlap score
    overlap = r_words & j_words
    match_score = round(100 * (len(overlap) / max(1, len(j_words))), 1)

    missing_keywords = sorted(list(j_words - r_words))[:50]

    ats_flags = []
    raw = (resume.raw_text or "").lower()
    for term in ATS_BANNED:
        if term in raw:
            ats_flags.append(f"Contains {term}")

    path_insights = [
        "Quantify achievements (%, $, time saved).",
        "Mirror top JD keywords in Summary and Skills.",
        "List current tools/frameworks relevant to the role.",
    ]

    return {
        "match_score": match_score,
        "missing_keywords": missing_keywords,
        "ats_flags": ats_flags,
        "path_insights": path_insights,
    }
