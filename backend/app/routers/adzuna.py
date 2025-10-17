from fastapi import APIRouter, HTTPException
import requests
import os

router = APIRouter()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

@router.get("/adzuna/health")
async def adzuna_health():
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return {"adzuna_configured": False, "status": "missing_credentials"}
    return {"adzuna_configured": True, "status": "healthy"}

@router.get("/adzuna/top-companies")
async def get_top_companies():
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise HTTPException(status_code=500, detail="Adzuna API credentials are not set")
    
    url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "results_per_page": 10,
        "what": "developer",
        "content-type": "application/json"
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Adzuna")
    
    data = response.json()
    companies = list(set([job.get("company", {}).get("display_name") for job in data.get("results", []) if job.get("company")]))
    return {"top_companies": companies[:5]}

@router.get("/adzuna/trending-industries")
async def get_trending_industries():
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise HTTPException(status_code=500, detail="Adzuna API credentials are not set")
    
    url = "https://api.adzuna.com/v1/api/categories"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "content-type": "application/json"
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch categories from Adzuna")
    
    data = response.json()
    categories = [cat.get("label") for cat in data.get("results", []) if cat.get("label")]
    return {"trending_industries": categories[:5]}

@router.get("/adzuna/hot-categories")
async def get_hot_categories():
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise HTTPException(status_code=500, detail="Adzuna API credentials are not set")
    
    url = "https://api.adzuna.com/v1/api/categories"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "content-type": "application/json"
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch categories from Adzuna")
    
    data = response.json()
    categories = [cat.get("label") for cat in data.get("results", []) if cat.get("label")]
    return {"hot_categories": categories[5:10]}

@router.get("/adzuna/market-insights")
async def get_market_insights():
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise HTTPException(status_code=500, detail="Adzuna API credentials are not set")
    
    url = "https://api.adzuna.com/v1/api/jobs/us/history"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": "software developer",
        "content-type": "application/json"
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch market insights from Adzuna")
    
    data = response.json()
    return {"market_insights": data.get("results", [])}

