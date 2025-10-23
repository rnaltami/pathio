from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Adzuna configuration
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

class JobSearchRequest(BaseModel):
    query: str
    location: Optional[str] = None

@router.get("/jobs/health")
def jobs_health():
    """Check if Adzuna API is configured"""
    return {
        "adzuna_configured": bool(ADZUNA_APP_ID and ADZUNA_API_KEY),
        "status": "healthy" if (ADZUNA_APP_ID and ADZUNA_API_KEY) else "missing_api_key"
    }

@router.post("/jobs/search")
def search_jobs(request: JobSearchRequest):
    """Search for jobs - COMPLETELY FRESH START"""
    
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise HTTPException(status_code=500, detail="Adzuna API keys not configured")
    
    try:
        # Simple API call - search with separate query and location
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_API_KEY,
            "what": request.query,
            "results_per_page": 50
        }
        
        if request.location:
            params["where"] = request.location
        else:
            # If no location provided, search for remote jobs
            params["what"] = request.query + " remote"
        
        print(f"Searching for: '{request.query}' in '{request.location}'")
        
        url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("results", [])
            
            # Simple job processing
            processed_jobs = []
            for job in jobs:
                processed_job = {
                    "title": job.get("title", ""),
                    "company": job.get("company", {}).get("display_name", ""),
                    "location": job.get("location", {}).get("display_name", ""),
                    "type": job.get("contract_type", ""),
                    "description": job.get("description", ""),
                    "url": job.get("redirect_url", ""),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "posted_at": job.get("created", "")
                }
                processed_jobs.append(processed_job)
            
            print(f"Found {len(processed_jobs)} jobs")
            return {"jobs": processed_jobs, "total": len(processed_jobs)}
        else:
            print(f"API error: {response.status_code}")
            return {"jobs": [], "total": 0}
            
    except Exception as e:
        print(f"Error: {e}")
        return {"jobs": [], "total": 0}
