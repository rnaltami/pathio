# backend/app/routers/jobs.py

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import requests
import re
import os

router = APIRouter()

# =========================
# Job Search Models
# =========================
class JobSearchRequest(BaseModel):
    job_title: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[str] = None
    user_resume: Optional[str] = None  # For personalized recommendations

class JobRecommendation(BaseModel):
    title: str
    company: str
    location: str
    type: str
    description: str
    requirements: List[str]
    match_score: int
    source: str = "mock"  # "indeed", "linkedin", "glassdoor", etc.
    url: Optional[str] = None

class JobAnalysisRequest(BaseModel):
    job_description: str
    user_resume: Optional[str] = None

# =========================
# Mock Job Data (for MVP)
# =========================
MOCK_JOBS = [
    {
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "type": "Full-time",
        "description": "We're looking for a Senior Software Engineer to join our growing team. You'll work on our core platform, building scalable systems and mentoring junior developers.",
        "requirements": ["Python", "React", "AWS", "5+ years experience", "Team leadership"],
        "match_score": 85,
        "source": "mock",
        "url": "https://example.com/job1"
    },
    {
        "title": "Full Stack Developer",
        "company": "StartupXYZ",
        "location": "Remote",
        "type": "Full-time",
        "description": "Join our innovative startup as a Full Stack Developer. You'll work on both frontend and backend systems, contributing to our product roadmap.",
        "requirements": ["JavaScript", "Node.js", "React", "MongoDB", "Startup experience"],
        "match_score": 72,
        "source": "mock",
        "url": "https://example.com/job2"
    },
    {
        "title": "Software Engineer II",
        "company": "BigTech Inc",
        "location": "Seattle, WA",
        "type": "Full-time",
        "description": "We're seeking a Software Engineer II to work on our core platform. You'll collaborate with cross-functional teams and contribute to system architecture.",
        "requirements": ["Java", "Spring", "Microservices", "3+ years experience", "Agile methodology"],
        "match_score": 68,
        "source": "mock",
        "url": "https://example.com/job3"
    },
    {
        "title": "Frontend Developer",
        "company": "DesignStudio",
        "location": "New York, NY",
        "type": "Full-time",
        "description": "Create beautiful, responsive user interfaces for our design platform. Work closely with designers and product managers.",
        "requirements": ["React", "TypeScript", "CSS", "UI/UX design", "2+ years experience"],
        "match_score": 75,
        "source": "mock",
        "url": "https://example.com/job4"
    },
    {
        "title": "Backend Engineer",
        "company": "DataFlow",
        "location": "Austin, TX",
        "type": "Full-time",
        "description": "Build and maintain our data processing pipeline. Work with large-scale systems and optimize performance.",
        "requirements": ["Python", "PostgreSQL", "Docker", "Data engineering", "4+ years experience"],
        "match_score": 80,
        "source": "mock",
        "url": "https://example.com/job5"
    }
]

# =========================
# Job Search Logic
# =========================
def _calculate_match_score(job: Dict[str, Any], user_resume: Optional[str] = None) -> int:
    """Calculate match score based on job requirements and user resume."""
    if not user_resume:
        # Return base score if no resume provided
        return job.get("match_score", 70)
    
    # Simple keyword matching for MVP
    resume_lower = user_resume.lower()
    requirements = job.get("requirements", [])
    
    matches = 0
    for req in requirements:
        if req.lower() in resume_lower:
            matches += 1
    
    if not requirements:
        return 70
    
    score = int((matches / len(requirements)) * 100)
    return max(50, min(95, score))  # Clamp between 50-95

def _filter_jobs(
    jobs: List[Dict[str, Any]], 
    job_title: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    skills: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Filter jobs based on search criteria."""
    filtered = jobs.copy()
    
    if job_title:
        job_title_lower = job_title.lower()
        filtered = [j for j in filtered if job_title_lower in j["title"].lower()]
    
    if location:
        location_lower = location.lower()
        filtered = [j for j in filtered if location_lower in j["location"].lower()]
    
    if company:
        company_lower = company.lower()
        filtered = [j for j in filtered if company_lower in j["company"].lower()]
    
    if skills:
        skills_lower = skills.lower()
        filtered = [j for j in filtered if any(
            skill.lower() in skills_lower for skill in j["requirements"]
        )]
    
    return filtered

# =========================
# Real API Integration
# =========================

# JSearch API Configuration
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "3284d8ef3amshbb37243bfa494e3p1620b1jsn405a5817b14c")
JSEARCH_HOST = "jsearch.p.rapidapi.com"

def fetch_jsearch_jobs(query: str, location: str = None, page: int = 1, num_pages: int = 1) -> List[Dict[str, Any]]:
    """Fetch jobs from JSearch API (RapidAPI) - PRIMARY SOURCE"""
    try:
        # Build search query
        search_query = query
        if location:
            search_query = f"{query} in {location}"
        
        url = "https://jsearch.p.rapidapi.com/search"
        params = {
            "query": search_query,
            "page": str(page),
            "num_pages": str(num_pages),
            "date_posted": "all"
        }
        
        headers = {
            "x-rapidapi-host": JSEARCH_HOST,
            "x-rapidapi-key": JSEARCH_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            jobs_data = data.get("data", [])
            
            # Transform to our format
            results = []
            for job in jobs_data:
                # Clean up description - keep full description (JSearch provides good ones)
                description = job.get("job_description", "")
                
                # Extract requirements from description or qualifications
                requirements = []
                qualifications = job.get("job_required_skills", [])
                if qualifications:
                    requirements = qualifications[:5]
                
                results.append({
                    "title": job.get("job_title", "Unknown"),
                    "company": job.get("employer_name", "Unknown"),
                    "location": job.get("job_city", job.get("job_state", job.get("job_country", "Remote"))),
                    "type": job.get("job_employment_type", "Full-time"),
                    "description": description,
                    "requirements": requirements,
                    "match_score": 75,  # Will be calculated based on resume
                    "source": "jsearch",
                    "url": job.get("job_apply_link", job.get("job_google_link", ""))
                })
            
            return results
        else:
            print(f"JSearch API error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"JSearch fetch error: {e}")
        return []

def fetch_remoteok_jobs(query: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch jobs from RemoteOK API"""
    try:
        url = "https://remoteok.com/api"
        headers = {'User-Agent': 'Pathio Job Platform (contact@pathio.ai)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            jobs = response.json()
            # First item is metadata, rest are jobs
            actual_jobs = jobs[1:] if len(jobs) > 1 else []
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                actual_jobs = [
                    j for j in actual_jobs
                    if query_lower in j.get('position', '').lower() or
                       any(query_lower in tag.lower() for tag in j.get('tags', []))
                ]
            
            # Transform to our format
            results = []
            for job in actual_jobs[:limit]:
                results.append({
                    "title": job.get('position', 'Unknown'),
                    "company": job.get('company', 'Unknown'),
                    "location": job.get('location', 'Remote'),
                    "type": "Remote",
                    "description": job.get('description', '')[:300] + "..." if job.get('description') else "",
                    "requirements": job.get('tags', [])[:5],
                    "match_score": 70,
                    "source": "remoteok",
                    "url": job.get('url', '')
                })
            
            return results
    except Exception as e:
        print(f"RemoteOK fetch error: {e}")
    return []

def fetch_themuse_jobs(query: str = None, page: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch jobs from TheMuse API"""
    try:
        url = "https://www.themuse.com/api/public/jobs"
        params = {'page': page, 'descending': 'true'}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('results', [])
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                jobs = [j for j in jobs if query_lower in j.get('name', '').lower()]
            
            # Transform to our format
            results = []
            for job in jobs[:limit]:
                company = job.get('company', {})
                locations = job.get('locations', [])
                location_str = locations[0].get('name', 'Unknown') if locations else 'Unknown'
                
                results.append({
                    "title": job.get('name', 'Unknown'),
                    "company": company.get('name', 'Unknown'),
                    "location": location_str,
                    "type": "Full-time",
                    "description": job.get('contents', '')[:300] + "..." if job.get('contents') else "",
                    "requirements": job.get('tags', [])[:5] if job.get('tags') else [],
                    "match_score": 70,
                    "source": "themuse",
                    "url": job.get('refs', {}).get('landing_page', '')
                })
            
            return results
    except Exception as e:
        print(f"TheMuse fetch error: {e}")
    return []

def fetch_arbeitnow_jobs(query: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch jobs from Arbeitnow API"""
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('data', [])
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                jobs = [j for j in jobs if query_lower in j.get('title', '').lower()]
            
            # Transform to our format
            results = []
            for job in jobs[:limit]:
                results.append({
                    "title": job.get('title', 'Unknown'),
                    "company": job.get('company_name', 'Unknown'),
                    "location": job.get('location', 'Unknown'),
                    "type": job.get('job_types', ['Full-time'])[0] if job.get('job_types') else 'Full-time',
                    "description": job.get('description', '')[:300] + "..." if job.get('description') else "",
                    "requirements": job.get('tags', [])[:5],
                    "match_score": 70,
                    "source": "arbeitnow",
                    "url": job.get('url', '')
                })
            
            return results
    except Exception as e:
        print(f"Arbeitnow fetch error: {e}")
    return []

# =========================
# Routes
# =========================
@router.post("/search-jobs")
def search_jobs(req: JobSearchRequest):
    """Search for jobs from multiple sources with JSearch as primary source."""
    
    all_jobs = []
    
    # PRIMARY: JSearch API (paid, high quality, diverse results)
    if req.job_title:
        jsearch_jobs = fetch_jsearch_jobs(
            query=req.job_title,
            location=req.location,
            page=1,
            num_pages=2  # Fetch 2 pages for more variety
        )
        all_jobs.extend(jsearch_jobs)
    
    # FALLBACK: Free APIs (if JSearch fails or for additional results)
    if len(all_jobs) < 10:
        all_jobs.extend(fetch_remoteok_jobs(req.job_title, limit=15))
        all_jobs.extend(fetch_themuse_jobs(req.job_title, limit=10))
        all_jobs.extend(fetch_arbeitnow_jobs(req.job_title, limit=10))
    
    # Last resort: mock data
    if not all_jobs:
        all_jobs = MOCK_JOBS.copy()
    
    # Filter by company if specified
    if req.company:
        company_lower = req.company.lower()
        all_jobs = [j for j in all_jobs if company_lower in j["company"].lower()]
    
    # Calculate match scores if resume provided
    if req.user_resume:
        for job in all_jobs:
            job["match_score"] = _calculate_match_score(job, req.user_resume)
    
    # Remove duplicates (same title + company)
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get("title", "").lower(), job.get("company", "").lower())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    # Sort by match score (highest first)
    unique_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Limit results
    results = unique_jobs[:20]
    
    return {
        "jobs": results,
        "total_found": len(unique_jobs),
        "showing": len(results),
        "search_criteria": {
            "job_title": req.job_title,
            "location": req.location,
            "company": req.company,
            "skills": req.skills
        },
        "sources_used": ["jsearch", "remoteok", "themuse", "arbeitnow"] if len(all_jobs) > 0 else ["mock"]
    }

@router.post("/analyze-job")
def analyze_job(req: JobAnalysisRequest):
    """Analyze a specific job posting and provide insights."""
    
    # For now, return basic analysis
    # In the future, this could use AI to extract key requirements, skills, etc.
    
    job_text = req.job_description
    requirements = []
    
    # Simple extraction of requirements (basic implementation)
    lines = job_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith(('•', '-', '*')) or 'required' in line.lower() or 'must have' in line.lower():
            requirements.append(line)
    
    return {
        "job_analysis": {
            "extracted_requirements": requirements[:10],  # Limit to 10
            "key_skills": [],  # Could be extracted with AI
            "experience_level": "mid-level",  # Could be determined with AI
            "company_culture_indicators": [],  # Could be extracted with AI
        },
        "recommendations": {
            "resume_focus_areas": [],
            "cover_letter_highlights": [],
            "skill_gaps": []
        }
    }

@router.get("/job-categories")
def get_job_categories():
    """Get popular job categories for search suggestions."""
    return {
        "categories": [
            {"name": "Software Engineering", "count": 45},
            {"name": "Data Science", "count": 23},
            {"name": "Product Management", "count": 18},
            {"name": "Marketing", "count": 31},
            {"name": "Sales", "count": 28},
            {"name": "Design", "count": 15},
            {"name": "Operations", "count": 22},
            {"name": "Finance", "count": 19}
        ]
    }

@router.get("/popular-skills")
def get_popular_skills():
    """Get popular skills for search suggestions."""
    return {
        "skills": [
            "Python", "JavaScript", "React", "Node.js", "AWS", "Docker",
            "SQL", "Machine Learning", "Data Analysis", "Project Management",
            "Agile", "Scrum", "Leadership", "Communication", "Problem Solving"
        ]
    }

