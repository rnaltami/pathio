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
    filter_type: Optional[str] = "remote"  # all, remote, hybrid, onsite
    employment_types: Optional[str] = None  # FULLTIME, CONTRACTOR, PARTTIME, INTERN
    job_requirements: Optional[str] = None  # under_3_years_experience, more_than_3_years_experience, no_experience, no_degree

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
# Job Type Categorization
# =========================
def categorize_job_type(job: Dict[str, Any]) -> str:
    """Categorize job as remote, hybrid, or onsite based on description and location."""
    description = (job.get("description") or "").lower()
    location = (job.get("location") or "").lower()
    title = (job.get("title") or "").lower()
    job_type = (job.get("type") or "").lower()
    
    # Check for remote keywords
    remote_keywords = ["remote", "work from home", "wfh", "virtual", "telecommute", "distributed"]
    if any(keyword in description or keyword in title for keyword in remote_keywords):
        return "remote"
    
    # Check for hybrid keywords
    hybrid_keywords = ["hybrid", "flexible", "partial remote", "2-3 days", "some remote", "mix of remote"]
    if any(keyword in description or keyword in title for keyword in hybrid_keywords):
        return "hybrid"
    
    # Check if location suggests remote (like "Remote", "Anywhere")
    if location in ["remote", "anywhere", "worldwide", "global"]:
        return "remote"
    
    # Default to onsite if not remote or hybrid
    return "onsite"

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

def fetch_jsearch_jobs(query: str, location: str = None, page: int = 1, num_pages: int = 1, filter_type: str = "remote", employment_types: str = None, job_requirements: str = None) -> List[Dict[str, Any]]:
    """Fetch jobs from JSearch API (RapidAPI) - PRIMARY SOURCE"""
    try:
        # Format query with + instead of spaces
        formatted_query = query.replace(" ", "+")
        url = "https://jsearch.p.rapidapi.com/search"
        params = {
            "query": formatted_query,
            "country": "us",
            "page": str(page),
            "num_pages": "3",
            "date_posted": "all"
        }
        
        # Simple filter logic based on API documentation
        if filter_type == "remote":
            # Remote jobs only
            params["work_from_home"] = "true"
            print(f"JSearch API call - query: {formatted_query}, work_from_home: true, country: us")
        elif filter_type == "all":
            # All job types (no work_from_home parameter)
            if location:
                params["location"] = location
            print(f"JSearch API call - query: {formatted_query}, all types, country: us, location: {location}")
        elif filter_type in ["hybrid", "onsite"]:
            # Hybrid/Onsite requires location
            if location:
                params["location"] = location
                print(f"JSearch API call - query: {formatted_query}, {filter_type} jobs, country: us, location: {location}")
            else:
                # Return empty for hybrid/onsite without location
                print(f"Skipping {filter_type} search - no location provided")
                return []
        
        # Add employment types if specified
        if employment_types:
            params["employment_types"] = employment_types
        
        # Add job requirements if specified
        if job_requirements:
            params["job_requirements"] = job_requirements
        
        headers = {
            "x-rapidapi-host": JSEARCH_HOST,
            "x-rapidapi-key": JSEARCH_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
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
                else:
                    # Fallback: extract from job description
                    desc = job.get("job_description", "")
                    if desc:
                        # Look for common requirement patterns
                        lines = desc.split('\n')
                        for line in lines[:20]:  # Check first 20 lines
                            line = line.strip().lower()
                            if any(word in line for word in ['required', 'must have', 'experience with', 'proficiency in', 'knowledge of']):
                                if len(line) < 100:  # Avoid long paragraphs
                                    requirements.append(line.capitalize())
                                    if len(requirements) >= 5:
                                        break
                
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

def fetch_adzuna_jobs(query: str, location: str = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch jobs from Adzuna API."""
    try:
        app_id = "a41fc845"
        app_key = "8b23dc5c36e989e62e8394bb41b1bacd"
        
        url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
        params = {
            'app_id': app_id,
            'app_key': app_key,
            'what': f"{query} remote",  # Add "remote" to search query for better results
            'results_per_page': limit
            # Note: Omitting 'location' parameter to get nationwide remote jobs
        }
        
        print(f"Adzuna API call with params: {params}")
        response = requests.get(url, params=params, timeout=30)
        print(f"Adzuna response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            jobs_data = data.get('results', [])
            
            # Transform to our format
            results = []
            for job in jobs_data:
                results.append({
                    "title": job.get("title", "Unknown"),
                    "company": job.get("company", {}).get("display_name", "Unknown"),
                    "location": job.get("location", {}).get("display_name", "Unknown"),
                    "type": "Full-time" if job.get("contract_time") == "full_time" else "Part-time",
                    "description": job.get("description", ""),
                    "requirements": [],  # Adzuna doesn't provide structured requirements
                    "match_score": 75,  # Default score
                    "source": "adzuna",
                    "url": job.get("redirect_url", ""),
                    "salary_min": job.get("salary_min", 0),
                    "salary_max": job.get("salary_max", 0),
                    "salary_is_predicted": job.get("salary_is_predicted", False),
                    "created": job.get("created", ""),
                    "category": job.get("category", {}).get("label", "")
                })
            
            return results
        else:
            print(f"Adzuna API error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Adzuna fetch error: {e}")
        return []

# =========================
# Routes
# =========================
@router.post("/search-jobs")
def search_jobs(req: JobSearchRequest):
    """Search for jobs from multiple sources with JSearch as primary source."""
    
    try:
        all_jobs = []
        
        # JSearch API - pass user's exact query, location, and filter type
        if req.job_title:
            print(f"Fetching JSearch jobs for: {req.job_title}, location: {req.location}, filter: {req.filter_type}")
            jsearch_jobs = fetch_jsearch_jobs(
                query=req.job_title,
                location=req.location,  # Pass user's location (None if not specified)
                page=1,
                num_pages=3,  # Get 3 pages for good coverage
                filter_type=req.filter_type,  # Pass filter type
                employment_types=req.employment_types,  # Pass employment types
                job_requirements=req.job_requirements  # Pass job requirements
            )
            print(f"Got {len(jsearch_jobs)} jobs from JSearch")
            all_jobs.extend(jsearch_jobs)
        
        # FALLBACK: Free APIs (if JSearch fails or for additional results)
        # Temporarily disabled to test JSearch and Adzuna with "remote" keyword
        # if len(all_jobs) < 50:
        #     all_jobs.extend(fetch_remoteok_jobs(req.job_title, limit=25))
        #     all_jobs.extend(fetch_themuse_jobs(req.job_title, limit=20))
        #     all_jobs.extend(fetch_arbeitnow_jobs(req.job_title, limit=20))
        
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
        
        # Add job type categorization to all jobs
        for job in all_jobs:
            job["job_type"] = categorize_job_type(job)
        
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
        results = unique_jobs[:50]  # Show more results
    
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
            "sources_used": ["jsearch"] if len(all_jobs) > 0 else ["mock"]
        }
    except Exception as e:
        print(f"Error in search_jobs: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@router.post("/test-api-sources")
def test_api_sources(req: JobSearchRequest):
    """Test each API source individually to see what they return."""
    results = {}
    
    # Test JSearch
    try:
        print(f"Testing JSearch for: {req.job_title}")
        jsearch_jobs = fetch_jsearch_jobs(
            query=req.job_title,
            location=None,
            page=1,
            num_pages=1
        )
        results["jsearch"] = {
            "count": len(jsearch_jobs),
            "sample_jobs": [
                {
                    "title": job.get("title"),
                    "location": job.get("location"),
                    "job_type": categorize_job_type(job),
                    "company": job.get("company")
                }
                for job in jsearch_jobs[:5]
            ]
        }
    except Exception as e:
        results["jsearch"] = {"error": str(e)}
    
    # Test Adzuna
    try:
        print(f"Testing Adzuna for: {req.job_title}")
        adzuna_jobs = fetch_adzuna_jobs(
            query=req.job_title,
            location=None,
            limit=10
        )
        results["adzuna"] = {
            "count": len(adzuna_jobs),
            "sample_jobs": [
                {
                    "title": job.get("title"),
                    "location": job.get("location"),
                    "job_type": categorize_job_type(job),
                    "company": job.get("company")
                }
                for job in adzuna_jobs[:5]
            ]
        }
    except Exception as e:
        results["adzuna"] = {"error": str(e)}
    
    return results

@router.post("/enhanced-job-search")
def enhanced_job_search(req: JobSearchRequest):
    """Enhanced job search with Perplexity-style comprehensive responses."""
    
    # Get regular job data
    job_response = search_jobs(req)
    jobs = job_response.get("jobs", [])
    
    # Create comprehensive response using AI
    if jobs and req.job_title:
        # Prepare data for AI synthesis
        jobs_summary = []
        for i, job in enumerate(jobs[:5], 1):  # Top 5 jobs
            # Include salary data if available (from Adzuna jobs)
            salary_info = ""
            if job.get("salary_min") and job.get("salary_max"):
                salary_min = int(job.get("salary_min", 0))
                salary_max = int(job.get("salary_max", 0))
                salary_info = f"${salary_min:,} - ${salary_max:,}"
                if job.get("salary_is_predicted"):
                    salary_info += " (estimated)"
            
            jobs_summary.append({
                "rank": i,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "type": job.get("type", ""),
                "match_score": job.get("match_score", 0),
                "requirements": job.get("requirements", [])[:3],  # Top 3 requirements
                "description_snippet": job.get("description", "")[:300] + "..." if job.get("description") else "",  # First 300 chars
                "salary": salary_info,
                "source": job.get("source", "")
            })
        
        # Create AI-powered comprehensive response
        comprehensive_response = _generate_comprehensive_job_response(
            job_title=req.job_title,
            location=req.location,
            jobs_summary=jobs_summary,
            total_found=job_response.get("total_found", 0),
            user_resume=req.user_resume
        )
        
        return {
            "comprehensive_response": comprehensive_response,
            "jobs": jobs,
            "total_found": job_response.get("total_found", 0),
            "showing": len(jobs),
            "search_criteria": {
                "job_title": req.job_title,
                "location": req.location,
                "company": req.company,
                "skills": req.skills
            }
        }
    
    return job_response

def _generate_comprehensive_job_response(job_title: str, location: str, jobs_summary: list, 
                                       total_found: int, user_resume: str = None) -> str:
    """Generate a Perplexity-style comprehensive response about job search results."""
    
    # Build the context for AI
    context = f"""
Job Search Query: {job_title} in {location or 'any location'}
Total Jobs Found: {total_found}

Top Job Opportunities:
"""
    
    for job in jobs_summary:
        salary_text = f" - Salary: {job['salary']}" if job['salary'] else ""
        context += f"""
{job['rank']}. {job['title']} at {job['company']} ({job['location']})
   - Match Score: {job['match_score']}%
   - Key Requirements: {', '.join(job['requirements']) if job['requirements'] else 'Not specified'}{salary_text}
   - Source: {job['source']}
   - Job Description: {job['description_snippet']}
"""
    
    if user_resume:
        context += f"\nUser Background: {user_resume[:500]}..."
    
    # AI prompt for comprehensive response
    prompt = f"""
You are Pathio, a career coach for Gen Z/Alpha. Create a comprehensive, Perplexity-style response about these EXACT job opportunities.

IMPORTANT: Use the SPECIFIC job data provided below. Do NOT give generic advice. Reference the actual companies, locations, and requirements listed.

Context: {context}

Generate a response that:
1. Starts with a compelling overview mentioning the EXACT number of jobs found ({total_found})
2. Highlights the top 3 most promising opportunities with SPECIFIC details from the data above
3. Uses the ACTUAL salary data provided in the job listings (if available)
4. Mentions the SPECIFIC companies and locations from the job data
5. References ACTUAL requirements from the job descriptions
6. Provides actionable next steps based on these specific opportunities
7. Uses an engaging, Gen Z-friendly tone but remains informative
8. Keeps it concise but comprehensive (300-400 words)

CRITICAL: Use the specific salary data provided for each job. If requirements say "Not specified", extract them from the job descriptions provided.

Format as markdown with clear sections and bullet points.
"""
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Pathio, a career coach for Gen Z/Alpha. Provide comprehensive, actionable career guidance with specific data and next steps."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"AI response generation error: {e}")
        # Fallback to basic response
        return f"""## {job_title} Jobs in {location or 'Various Locations'}

Found **{total_found} opportunities** across multiple job boards.

### Top Opportunities:
{chr(10).join([f"**{i+1}.** {job['title']} at {job['company']} ({job['match_score']}% match)" + (f" - {job['salary']}" if job['salary'] else "") for i, job in enumerate(jobs_summary[:3])])}

### Next Steps:
- Review job requirements and tailor your resume
- Apply to top matches within 48 hours
- Follow up with hiring managers on LinkedIn

*Data sourced from multiple job boards including JSearch and Adzuna.*"""

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

