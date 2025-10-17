from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
from docx import Document
from io import BytesIO
import base64

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# OpenAI client will be initialized when needed

class TailorRequest(BaseModel):
    job_description: str
    resume: str

class DownloadRequest(BaseModel):
    content: str

@router.post("/tailor/generate")
def generate_tailored_content(request: TailorRequest):
    """Generate tailored resume and cover letter"""
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        # Generate tailored resume
        resume_prompt = f"""
        You are an expert resume writer. Based on the following job description, tailor this resume to match the requirements and keywords.
        
        Job Description:
        {request.job_description}
        
        Original Resume:
        {request.resume}
        
        Please provide a tailored resume that:
        1. Incorporates relevant keywords from the job description
        2. Highlights relevant experience and skills
        3. Matches the tone and requirements of the role
        4. Maintains professional formatting
        
        Return only the tailored resume content.
        """
        
        resume_response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": resume_prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        tailored_resume = resume_response.choices[0].message.content
        
        # Generate cover letter
        cover_letter_prompt = f"""
        You are an expert cover letter writer. Write a compelling cover letter for this job based on the resume.
        
        Job Description:
        {request.job_description}
        
        Resume:
        {request.resume}
        
        Please write a cover letter that:
        1. Demonstrates enthusiasm for the role
        2. Highlights relevant experience from the resume
        3. Shows understanding of the company/role
        4. Is professional and engaging
        
        Return only the cover letter content.
        """
        
        cover_letter_response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": cover_letter_prompt}],
            max_tokens=800,
            temperature=0.7
        )
        
        cover_letter = cover_letter_response.choices[0].message.content
        
        return {
            "tailored_resume": tailored_resume,
            "cover_letter": cover_letter
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

@router.post("/tailor/download")
def download_document(request: DownloadRequest):
    """Convert text content to DOCX and return as base64"""
    
    try:
        # Create a new Document
        doc = Document()
        
        # Add content to document
        paragraphs = request.content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                doc.add_paragraph(paragraph.strip())
        
        # Save to BytesIO
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        # Convert to base64
        file_data = buffer.getvalue()
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        return {"file_data": base64_data, "filename": "document.docx"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")
