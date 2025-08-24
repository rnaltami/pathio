# backend/app/routers/public.py

from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from ..models import ResumeJSON, JobPostingJSON
from ..resume_parser import parse_resume
from ..jd_extractor import extract_job
from ..tailor import tailor_documents
from ..insights import compute_insights

from io import BytesIO
from fastapi.responses import StreamingResponse
from ..docx_export import export_docx

router = APIRouter()


# -------- Request Schemas --------
class ExtractJobReq(BaseModel):
    url: Optional[str] = None
    pasted_text: Optional[str] = None


class TailorReq(BaseModel):
    resume_json: ResumeJSON
    job_json: JobPostingJSON
    user_tweaks: Optional[Dict[str, Any]] = None


class ExportReq(BaseModel):
    tailored_resume_md: str
    cover_letter_md: Optional[str] = None
    which: str = "resume"  # "resume" or "cover"


# -------- Routes --------
@router.post("/parse-resume", response_model=ResumeJSON)
async def parse_resume_ep(file: UploadFile = File(...)):
    try:
        return await parse_resume(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/extract-job", response_model=JobPostingJSON)
async def extract_job_ep(payload: ExtractJobReq):
    """
    Accepts either/both of:
      - payload.url  (scrape if possible)
      - payload.pasted_text (always allowed)
    Returns: JobPostingJSON with raw_text + extracted keywords.
    """
    # Allow paste-only flow cleanly:
    url = payload.url or None
    pasted = (payload.pasted_text or "").strip()

    if not url and not pasted:
        raise HTTPException(status_code=400, detail="Provide url or pasted_text.")

    try:
        # Our extractor already knows how to handle (url, pasted_text)
        # It should prefer pasted_text when present, otherwise scrape URL.
        return await extract_job(url, pasted)
    except ValueError as ve:
        # Known friendly errors from extractor
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to import job. Please paste the job description text."
        )


@router.post("/tailor")
async def tailor_ep(payload: TailorReq):
    try:
        return await tailor_documents(
            payload.resume_json,
            payload.job_json,
            payload.user_tweaks or {}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/insights")
async def insights_ep(payload: TailorReq):
    try:
        return await compute_insights(payload.resume_json, payload.job_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export")
async def export_ep(payload: ExportReq):
    md = payload.tailored_resume_md if payload.which == "resume" else (payload.cover_letter_md or "")
    if not md.strip():
        raise HTTPException(status_code=400, detail="No content to export.")

    bio = BytesIO()
    export_docx(md, bio)
    bio.seek(0)
    filename = f"pathio_{payload.which}.docx"
    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
