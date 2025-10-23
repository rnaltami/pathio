from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

class JobAnalysisRequest(BaseModel):
    jobDescription: str
    resume: str

class JobAnalysisResponse(BaseModel):
    jobTitle: str
    matchScore: int
    improvements: list[str]
    dailyTasks: list[str]
    canTailor: bool

@router.post("/help-me-apply", response_model=JobAnalysisResponse)
async def analyze_job_match(request: JobAnalysisRequest):
    try:
        # Extract job title from job description
        job_title = extract_job_title(request.jobDescription)
        
        # Analyze the match between resume and job
        analysis = await analyze_resume_job_match(request.resume, request.jobDescription)
        
        return JobAnalysisResponse(
            jobTitle=job_title,
            matchScore=analysis["match_score"],
            improvements=analysis["improvements"],
            dailyTasks=analysis["daily_tasks"],
            canTailor=analysis["can_tailor"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_job_title(job_description: str) -> str:
    """Extract job title from job description"""
    lines = job_description.split('\n')
    first_line = lines[0].strip() if lines else ""
    
    # If first line is short and looks like a title, use it
    if first_line and len(first_line) < 100 and not first_line.lower().startswith(('company', 'location', 'salary')):
        return first_line
    
    # Try to find common job title patterns
    job_title_keywords = [
        'software engineer', 'developer', 'manager', 'analyst', 'specialist',
        'coordinator', 'director', 'lead', 'senior', 'junior', 'intern'
    ]
    
    for keyword in job_title_keywords:
        if keyword.lower() in job_description.lower():
            # Find the line containing the keyword and extract a reasonable title
            for line in lines[:5]:  # Check first 5 lines
                if keyword.lower() in line.lower():
                    return line.strip()
    
    return "This Position"

async def analyze_resume_job_match(resume: str, job_description: str) -> dict:
    """Analyze how well the resume matches the job requirements"""
    
    prompt = f"""
    Analyze how well this resume matches the job requirements and provide specific, actionable feedback.

    JOB DESCRIPTION:
    {job_description}

    RESUME:
    {resume}

    Please provide:
    1. A match score (0-100) based on skills, experience, and qualifications
    2. Exactly 3 specific, actionable improvements the candidate can make to their resume
    3. Exactly 3 things the candidate can do TODAY to improve their skillset for this role
    4. Whether the resume can be tailored to better match this job (true/false)

    Format your response as JSON:
    {{
        "match_score": 75,
        "improvements": [
            "Add specific examples of [relevant skill] from your experience",
            "Highlight your [relevant experience] that matches the job requirements",
            "Include keywords from the job posting like '[keyword1]' and '[keyword2]'"
        ],
        "daily_tasks": [
            "Take a free online course on [specific skill] (Coursera, edX, or YouTube)",
            "Practice [specific skill] with a hands-on project or tutorial",
            "Read articles or watch videos about [industry trend] to stay current"
        ],
        "can_tailor": true
    }}

    Focus on:
    - Skills alignment
    - Experience relevance
    - Keyword matching
    - Specific, actionable advice
    - Whether tailoring would significantly improve the match
    """

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a career coach helping candidates improve their job applications. Provide specific, actionable feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse the JSON response
        import json
        result = json.loads(response.choices[0].message.content)
        
        return {
            "match_score": result.get("match_score", 50),
            "improvements": result.get("improvements", ["Improve your resume", "Add more details", "Highlight relevant experience"]),
            "daily_tasks": result.get("daily_tasks", ["Take an online course", "Practice relevant skills", "Research industry trends"]),
            "can_tailor": result.get("can_tailor", True)
        }
        
    except Exception as e:
        # Fallback analysis if OpenAI fails
        return {
            "match_score": 60,
            "improvements": [
                "Add more specific examples of your achievements",
                "Include keywords from the job posting",
                "Highlight relevant skills and experience"
            ],
            "daily_tasks": [
                "Take a free online course on relevant skills (Coursera, edX, or YouTube)",
                "Practice the required skills with hands-on projects",
                "Read industry articles and stay updated on trends"
            ],
            "can_tailor": True
        }

@router.post("/tailor-resume")
async def tailor_resume(request: dict):
    """Tailor the resume to better match the job requirements"""
    try:
        job_description = request.get("jobDescription", "")
        resume = request.get("resume", "")
        analysis = request.get("analysis", {})
        
        tailored_resume = await create_tailored_resume(resume, job_description, analysis)
        
        return tailored_resume
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_tailored_resume(resume: str, job_description: str, analysis: dict) -> str:
    """Create a tailored version of the resume"""
    
    prompt = f"""
    Tailor this resume to better match the job requirements. Keep the original structure but enhance it to be more relevant to the specific job.

    JOB DESCRIPTION:
    {job_description}

    ORIGINAL RESUME:
    {resume}

    ANALYSIS FEEDBACK:
    Match Score: {analysis.get('match_score', 0)}%
    Improvements: {', '.join(analysis.get('improvements', []))}

    Please:
    1. Keep the same basic structure and format
    2. Add relevant keywords from the job posting
    3. Emphasize skills and experience that match the job requirements
    4. Add specific examples where possible
    5. Make the resume more compelling for this specific role

    Return the tailored resume as plain text.
    """

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional resume writer specializing in tailoring resumes for specific job applications."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Fallback: return original resume with a note
        return f"{resume}\n\n--- TAILORED FOR THIS POSITION ---\n\nNote: Resume tailoring failed. Please manually incorporate the suggested improvements."
