# backend/app/jd_extractor.py

from __future__ import annotations
from typing import Optional, List
import re
import requests
from bs4 import BeautifulSoup

from .models import JobPostingJSON

# --- simple stopword list for keyword extraction
_STOP = {
    "the","and","for","with","that","this","from","your","you","are","our","about","will",
    "have","has","was","were","not","but","all","any","can","may","such","into","over",
    "more","most","other","their","there","then","than","been","being","also","able",
    "job","role","description","requirements","responsibilities","preferred","minimum",
    "experience","years","work","skills","team","teams","ability","including","etc","using",
    "on","in","to","of","a","an","as","by","at","or","it","is","be","we","us"
}

def _clean(text: str) -> str:
    if not text:
        return ""
    # strip scripts/styles and HTML tags if someone pasted HTML
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    # collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()

def _looks_like_noise(text: str) -> bool:
    # crude heuristic to reject themey JS soup pages
    braces = text.count("{") + text.count("}")
    scripts = text.lower().count("<script")
    tokens = len(text.split())
    return braces > 50 or scripts > 5 or tokens < 50

def _keywords(text: str, k: int = 50) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+\-_/]{1,}", text.lower())
    freq = {}
    for w in words:
        if w in _STOP or len(w) < 3:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:k]]

def _guess_title_company_location(text: str):
    # very light heuristics: look for "Title: ..." / "Company: ..." / location-like tokens
    title = None
    company = None
    location = None

    m = re.search(r"(?im)^\s*(title)\s*[:\-]\s*(.+)$", text)
    if m:
        title = m.group(2).strip()

    m = re.search(r"(?im)^\s*(company)\s*[:\-]\s*(.+)$", text)
    if m:
        company = m.group(2).strip()

    # naive location guess: "City, ST" or "City, State" or common words like "Los Angeles, CA"
    m = re.search(r"(?im)\b([A-Za-z][A-Za-z .'-]+,\s?(?:[A-Z]{2}|[A-Za-z .'-]+))\b", text)
    if m:
        location = m.group(1).strip()

    return title, company, location

async def extract_job(url: Optional[str], pasted_text: Optional[str]) -> JobPostingJSON:
    """
    Prefer pasted_text. If provided, clean and return immediately.
    Otherwise, try to fetch and extract from URL.
    """
    # --- 1) PASTE-FIRST PATH
    if pasted_text and pasted_text.strip():
        raw = _clean(pasted_text)
        title, company, location = _guess_title_company_location(raw)
        return JobPostingJSON(
            url=None,
            title=title,
            company=company,
            location=location,
            raw_text=raw,
            extracted_keywords=_keywords(raw),
        )

    # --- 2) URL SCRAPE (fallback)
    if url:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/126.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # try common containers first
            main = soup.find(attrs={"id": re.compile(r"(job|posting)", re.I)}) or \
                   soup.find(attrs={"class": re.compile(r"(job|posting|description)", re.I)}) or \
                   soup

            raw = _clean(main.get_text("\n", strip=True))
            if _looks_like_noise(raw):
                raise ValueError("Unable to import job. Please paste the job description text.")

            # light meta extraction
            title = None
            meta_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find("meta", attrs={"name": "title"})
            if meta_title and meta_title.get("content"):
                title = meta_title.get("content").strip()
            company = None
            meta_site = soup.find("meta", attrs={"property": "og:site_name"})
            if meta_site and meta_site.get("content"):
                company = meta_site.get("content").strip()

            if not title:
                guessed_title, guessed_company, guessed_loc = _guess_title_company_location(raw)
                title = title or guessed_title
                company = company or guessed_company
                location = guessed_loc
            else:
                _, guessed_company, location = _guess_title_company_location(raw)
                company = company or guessed_company

            return JobPostingJSON(
                url=url,
                title=title,
                company=company,
                location=location,
                raw_text=raw,
                extracted_keywords=_keywords(raw),
            )
        except ValueError as ve:
            # pass through friendly messages
            raise ve
        except Exception:
            # generic scrape failure
            raise ValueError("Unable to import job. Please paste the job description text.")

    # --- 3) neither provided
    raise ValueError("Provide url or pasted_text.")
