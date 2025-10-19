from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
from app.routers import jobs

load_dotenv()

app = FastAPI()

# Include routers
app.include_router(jobs.router, prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    market_data: dict
    sources: list
    web_results: list

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Perplexity client
perplexity_client = openai.OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai"
)

@app.get("/")
async def root():
    return {"message": "Pathio Backend - Intelligent Career Chat"}

async def fetch_perplexity_web_results(query: str) -> dict:
    """Fetch real-time web search results from Perplexity"""
    try:
        response = perplexity_client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "user", "content": query}
            ],
            extra_body={
                "search_mode": "web",
                "search_recency_filter": "month",
                "max_results": 10
            },
            max_tokens=800,
            temperature=0.1
        )
        
        # Extract search results and citations
        search_results = []
        if hasattr(response, 'search_results') and response.search_results:
            for result in response.search_results:
                search_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", ""),
                    "date": result.get("date", "")
                })
        
        return {
            "content": response.choices[0].message.content,
            "search_results": search_results
        }
    except Exception as e:
        print(f"Perplexity API error: {e}")
        return {"content": "", "search_results": []}

async def fetch_adzuna_market_data(query: str) -> dict:
    """Fetch job market data from Adzuna"""
    try:
        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")
        
        if not app_id or not app_key:
            return {"error": "Adzuna API keys not configured"}
        
        # Extract job title from query
        job_title = query.lower()
        if "discord" in job_title:
            job_title = "software engineer"
        elif "data" in job_title:
            job_title = "data scientist"
        elif "marketing" in job_title:
            job_title = "marketing manager"
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": job_title,
                "results_per_page": 10,
                "content-type": "application/json"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "total_jobs": data.get("count", 0),
                        "jobs": data.get("results", [])[:5],  # Top 5 jobs
                        "salary_info": {
                            "min": min([job.get("salary_min", 0) for job in data.get("results", []) if job.get("salary_min")]),
                            "max": max([job.get("salary_max", 0) for job in data.get("results", []) if job.get("salary_max")])
                        } if data.get("results") else {}
                    }
                else:
                    return {"error": f"Adzuna API error: {response.status}"}
    except Exception as e:
        print(f"Adzuna API error: {e}")
        return {"error": str(e)}

def synthesize_web_results(perplexity_data: dict, adzuna_data: dict) -> str:
    """Synthesize web results into structured insights"""
    insights = []
    
    # Add Perplexity insights
    if perplexity_data.get("content"):
        insights.append(f"Web Research: {perplexity_data['content'][:200]}...")
    
    # Add Adzuna insights
    if adzuna_data.get("total_jobs", 0) > 0:
        insights.append(f"Job Market: {adzuna_data['total_jobs']} active positions found")
        if adzuna_data.get("salary_info", {}).get("min"):
            insights.append(f"Salary Range: ${adzuna_data['salary_info']['min']:,} - ${adzuna_data['salary_info']['max']:,}")
    
    return "\n".join(insights)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Run Perplexity and Adzuna in parallel
        perplexity_task = asyncio.create_task(fetch_perplexity_web_results(request.message))
        adzuna_task = asyncio.create_task(fetch_adzuna_market_data(request.message))
        
        # Wait for both to complete
        perplexity_data, adzuna_data = await asyncio.gather(perplexity_task, adzuna_task)
        
        # Synthesize the data
        synthesized_insights = synthesize_web_results(perplexity_data, adzuna_data)
        
        # Create comprehensive prompt for OpenAI
        system_prompt = """You are an intelligent career coach providing Perplexity-style responses. Structure your answer with these exact sections:

**Summary** - Brief 2-3 sentence overview
**Key Insights** - Bullet points with specific data and insights
**Current Trends** - Market trends and industry developments  
**Market Intelligence** - Salary data, job availability, company insights
**Next Steps** - Specific actionable recommendations

Use bullet points (-) for all lists. Be concise but comprehensive. Include specific numbers, companies, and data when available."""

        user_prompt = f"""User Question: {request.message}

Web Research Insights:
{perplexity_data.get('content', 'No web research available')}

Market Data:
{synthesized_insights}

Provide a structured response following the exact format specified in the system prompt."""

        # Generate response with OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extract sources from Perplexity
        sources = []
        for result in perplexity_data.get("search_results", []):
            if result.get("url"):
                sources.append({
                    "title": result.get("title", "Web Source"),
                    "url": result.get("url")
                })
        
        return ChatResponse(
            reply=response.choices[0].message.content,
            market_data=adzuna_data,
            sources=sources,
            web_results=perplexity_data.get("search_results", [])
        )
    
    except Exception as e:
        return ChatResponse(
            reply=f"Sorry, I encountered an error: {str(e)}",
            market_data={},
            sources=[],
            web_results=[]
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)