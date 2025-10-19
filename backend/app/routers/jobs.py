from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")

class JobSearchRequest(BaseModel):
    query: str
    location: str = None
    job_type: str = None

@router.get("/jobs/health")
def jobs_health():
    """Check if JSearch API is configured"""
    return {
        "jsearch_configured": bool(JSEARCH_API_KEY),
        "status": "healthy" if JSEARCH_API_KEY else "missing_api_key"
    }

def fetch_jsearch_jobs(query: str, location: str = None, job_type: str = None):
    """Fetch jobs from JSearch API (RapidAPI version)"""
    if not JSEARCH_API_KEY:
        return []
    
    # Build search parameters
    search_params = {
        "query": query,
        "page": 1,
        "num_pages": 3
    }
    
    # Add location to query if provided
    if location:
        search_params["query"] = f"{query} in {location}"
    
    # Set remote work preference
    if job_type == "remote":
        search_params["work_from_home"] = True
    elif job_type in ["hybrid", "onsite"]:
        search_params["work_from_home"] = False
        if location:
            search_params["query"] = f"{query} jobs in {location}"
    
    try:
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": JSEARCH_API_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=search_params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            jobs_data = data.get("data", [])
            
            processed_jobs = []
            for job in jobs_data:
                # Safely handle location concatenation
                city = job.get("job_city", "") or ""
                state = job.get("job_state", "") or ""
                location = f"{city}, {state}".strip(", ") if city or state else "Remote"
                
                processed_job = {
                    "title": job.get("job_title", ""),
                    "company": job.get("employer_name", ""),
                    "location": location,
                    "type": job.get("job_employment_type", ""),
                    "description": job.get("job_description", ""),
                    "url": job.get("job_apply_link", ""),
                    "salary_min": job.get("job_min_salary"),
                    "salary_max": job.get("job_max_salary"),
                    "job_type": job_type or "all"
                }
                processed_jobs.append(processed_job)
            
            return processed_jobs
        else:
            print(f"JSearch API error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching jobs from JSearch: {e}")
        return []

@router.post("/jobs/search")
def search_jobs(request: JobSearchRequest):
    """Search for jobs using JSearch API"""
    
    if not JSEARCH_API_KEY:
        raise HTTPException(status_code=500, detail="JSearch API key not configured")
    
    try:
        jobs = fetch_jsearch_jobs(request.query, request.location, request.job_type)
        return {"jobs": jobs, "total": len(jobs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

