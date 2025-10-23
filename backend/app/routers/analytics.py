from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import openai
import os
import json
import re
import tempfile
from dotenv import load_dotenv
import PyPDF2
from docx import Document

load_dotenv()

router = APIRouter()

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ResumeAnalysisRequest(BaseModel):
    resume_text: str

class ResumeAnalysisResponse(BaseModel):
    skills: List[str]
    experience_years: int
    current_role: str
    career_level: str
    market_value: Dict[str, Any]
    recommendations: List[str]
    skill_gaps: List[str]
    salary_insights: Dict[str, Any]
    industry_insights: Dict[str, Any]

def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from uploaded file (PDF, DOCX, TXT)"""
    try:
        # Read file content
        content = file.file.read()
        
        if file.filename.endswith('.pdf'):
            # Extract text from PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                
                os.unlink(tmp_file.name)
                return text.strip()
                
        elif file.filename.endswith(('.docx', '.doc')):
            # Extract text from DOCX
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                
                doc = Document(tmp_file.name)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                
                os.unlink(tmp_file.name)
                return text.strip()
                
        elif file.filename.endswith('.txt'):
            # Extract text from TXT
            return content.decode('utf-8').strip()
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, or TXT files.")
            
    except Exception as e:
        print(f"Error extracting text from file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text from file: {str(e)}")

def extract_resume_data(resume_text: str) -> Dict[str, Any]:
    """Extract structured data from resume text using OpenAI"""
    
    extraction_prompt = f"""
    Analyze this resume and extract the following information in JSON format:
    
    {{
        "skills": ["skill1", "skill2", "skill3"],
        "experience_years": 5,
        "current_role": "Software Engineer",
        "career_level": "Mid-level",
        "education": "Bachelor's in Computer Science",
        "certifications": ["AWS Certified", "Google Cloud"],
        "previous_roles": ["Junior Developer", "Software Engineer"],
        "industries": ["Technology", "Finance"],
        "technologies": ["Python", "React", "AWS"],
        "achievements": ["Led team of 5", "Increased efficiency by 30%"]
    }}
    
    Resume text:
    {resume_text}
    
    Return only valid JSON, no additional text.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        
        # Parse JSON response
        content = response.choices[0].message.content.strip()
        # Remove any markdown formatting
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"Error extracting resume data: {e}")
        return {}

def analyze_career_insights(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate career insights and recommendations"""
    
    analysis_prompt = f"""
    As a career coach, analyze this resume data and provide insights:
    
    Resume Data: {json.dumps(resume_data, indent=2)}
    
    Provide analysis in this JSON format:
    {{
        "market_value": {{
            "estimated_salary_min": 80000,
            "estimated_salary_max": 120000,
            "market_demand": "High",
            "growth_potential": "Strong"
        }},
        "recommendations": [
            "Consider getting AWS certification",
            "Learn machine learning frameworks",
            "Build leadership experience"
        ],
        "skill_gaps": [
            "Cloud architecture",
            "DevOps practices",
            "Team leadership"
        ],
        "salary_insights": {{
            "current_range": "80k-120k",
            "next_level_range": "120k-160k",
            "industry_average": "95k"
        }},
        "industry_insights": {{
            "trending_skills": ["AI/ML", "Cloud", "DevOps"],
            "growth_areas": ["Fintech", "Healthtech", "Edtech"],
            "remote_opportunities": "High"
        }}
    }}
    
    Return only valid JSON, no additional text.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"Error analyzing career insights: {e}")
        return {}

@router.post("/analytics/resume", response_model=ResumeAnalysisResponse)
def analyze_resume(request: ResumeAnalysisRequest):
    """Analyze resume and provide career insights"""
    
    try:
        # Extract structured data from resume
        resume_data = extract_resume_data(request.resume_text)
        
        if not resume_data:
            raise HTTPException(status_code=400, detail="Failed to extract resume data")
        
        # Generate career insights
        insights = analyze_career_insights(resume_data)
        
        # Combine data for response
        return ResumeAnalysisResponse(
            skills=resume_data.get("skills", []),
            experience_years=resume_data.get("experience_years", 0),
            current_role=resume_data.get("current_role", ""),
            career_level=resume_data.get("career_level", ""),
            market_value=insights.get("market_value", {}),
            recommendations=insights.get("recommendations", []),
            skill_gaps=insights.get("skill_gaps", []),
            salary_insights=insights.get("salary_insights", {}),
            industry_insights=insights.get("industry_insights", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {str(e)}")

@router.post("/analytics/resume-upload", response_model=ResumeAnalysisResponse)
async def analyze_resume_upload(file: UploadFile = File(...)):
    """Analyze uploaded resume file and provide career insights"""
    
    try:
        # Extract text from uploaded file
        resume_text = extract_text_from_file(file)
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="No text found in uploaded file")
        
        # Extract structured data from resume
        resume_data = extract_resume_data(resume_text)
        
        if not resume_data:
            raise HTTPException(status_code=400, detail="Failed to extract resume data")
        
        # Generate career insights
        insights = analyze_career_insights(resume_data)
        
        # Combine data for response
        return ResumeAnalysisResponse(
            skills=resume_data.get("skills", []),
            experience_years=resume_data.get("experience_years", 0),
            current_role=resume_data.get("current_role", ""),
            career_level=resume_data.get("career_level", ""),
            market_value=insights.get("market_value", {}),
            recommendations=insights.get("recommendations", []),
            skill_gaps=insights.get("skill_gaps", []),
            salary_insights=insights.get("salary_insights", {}),
            industry_insights=insights.get("industry_insights", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {str(e)}")

@router.get("/analytics/health")
def analytics_health():
    """Check if analytics service is working"""
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }
