from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import requests
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"OpenAI import failed: {e}")
    OPENAI_AVAILABLE = False
    OpenAI = None
from typing import List, Dict, Any

router = APIRouter()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Adzuna configuration
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

# Perplexity configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Initialize client as None - will be created when needed
client = None

def get_openai_client():
    """Get OpenAI client, creating it if needed"""
    if OPENAI_API_KEY and OPENAI_AVAILABLE:
        return OpenAI(api_key=OPENAI_API_KEY)
    return None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []
    next_steps: List[str] = []
    market_data: Dict[str, Any] = {}
    web_results: List[Dict[str, Any]] = []

def extract_career_terms(message: str) -> List[str]:
    """Extract potential career/job terms from user message"""
    career_keywords = [
        'engineer', 'developer', 'data scientist', 'analyst', 'manager', 'designer',
        'marketing', 'sales', 'finance', 'accounting', 'nurse', 'teacher', 'lawyer',
        'doctor', 'researcher', 'consultant', 'product', 'operations', 'hr',
        'human resources', 'software', 'web', 'mobile', 'frontend', 'backend',
        'full stack', 'devops', 'cloud', 'ai', 'machine learning', 'cyber',
        'security', 'project', 'business', 'strategy', 'content', 'writer',
        'journalist', 'editor', 'photographer', 'artist', 'musician', 'actor',
        'astronaut', 'pilot', 'mechanic', 'electrician', 'plumber', 'chef',
        'architect', 'engineer', 'scientist', 'researcher'
    ]
    
    message_lower = message.lower()
    found_terms = []
    
    for keyword in career_keywords:
        if keyword in message_lower:
            found_terms.append(keyword)
    
    # If no specific terms found, try to extract general career-related words
    if not found_terms:
        words = message_lower.split()
        for word in words:
            if len(word) > 4 and any(char.isalpha() for char in word):
                if 'job' in word or 'career' in word or 'work' in word or 'profession' in word:
                    found_terms.append(word)
    
    return found_terms[:3]  # Return top 3 terms

def fetch_adzuna_market_data(terms: List[str]) -> Dict[str, Any]:
    """Fetch market insights from Adzuna for given career terms"""
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY or not terms:
        return {}
    
    market_data = {
        'top_companies': [],
        'trending_industries': [],
        'salary_insights': [],
        'market_trends': []
    }
    
    try:
        # Get top companies for the first term
        if terms:
            primary_term = terms[0]
            
            # Fetch job search data for salary insights
            url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_API_KEY,
                "results_per_page": 10,
                "what": primary_term,
                "content-type": "application/json"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("results", [])
                
                # Extract companies
                companies = list(set([
                    job.get("company", {}).get("display_name") 
                    for job in jobs 
                    if job.get("company", {}).get("display_name")
                ]))
                market_data['top_companies'] = companies[:5]
                
                # Extract salary data
                salaries = []
                for job in jobs:
                    salary_min = job.get("salary_min")
                    salary_max = job.get("salary_max")
                    if salary_min and salary_max:
                        salaries.append({
                            "min": salary_min,
                            "max": salary_max,
                            "company": job.get("company", {}).get("display_name", "Unknown")
                        })
                
                market_data['salary_insights'] = salaries[:5]
                
                # Get trending industries
                market_data['trending_industries'] = [
                    job.get("category", {}).get("label", "Technology") 
                    for job in jobs[:5] 
                    if job.get("category")
                ]
            
    except Exception as e:
        print(f"Error fetching Adzuna data: {e}")
        return {}
    
    return market_data

def fetch_perplexity_web_results(message: str) -> List[Dict[str, Any]]:
    """Fetch web search results from Perplexity API"""
    if not PERPLEXITY_API_KEY:
        return []
    
    try:
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Create a more focused search prompt
        search_prompt = f"Find recent career trends and insights about: {message}. Include salary data, job market trends, and industry developments."
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a career research assistant. Provide current, accurate information about job markets, salaries, and career trends. Focus on recent data and specific insights."
                },
                {
                    "role": "user",
                    "content": search_prompt
                }
            ],
            "max_tokens": 600,  # Reduced for faster response
            "temperature": 0.1,  # Lower temperature for more focused results
            "extra_body": {
                "search_mode": "web",
                "search_recency_filter": "month"
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            search_results = data.get("search_results", [])
            
            # Parse the response for structured information
            web_results = []
            
            # First, extract key insights from the main content
            lines = content.split('\n')
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('**') and line.endswith('**'):
                    current_section = line.replace('**', '')
                elif line and not line.startswith('[') and len(line) > 20:
                    web_results.append({
                        "content": line,
                        "section": current_section,
                        "source": "Perplexity Web Search"
                    })
            
            # Add search results as additional sources
            for result in search_results[:3]:  # Limit to 3 sources
                title = result.get("title", "Web Source")
                url = result.get("url", "")
                snippet = result.get("snippet", "")
                
                web_results.append({
                    "content": f"{title}: {snippet}" if snippet else title,
                    "section": "Web Sources",
                    "source": url if url else "Web"
                })
            
            return web_results[:5]  # Return top 5 results
            
    except requests.exceptions.Timeout:
        print("Perplexity API timeout - continuing without web search results")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Perplexity API request error: {e}")
        return []
    except Exception as e:
        print(f"Error fetching Perplexity data: {e}")
        return []
    
    return []

def get_career_coaching_prompt(user_message: str, conversation_history: List[ChatMessage], market_data: Dict[str, Any], web_results: List[Dict[str, Any]]) -> str:
    """Generate a prompt for career coaching with Perplexity-style structure"""
    
    system_prompt = """You are a career coach and job search expert. Provide rich, grounded responses like Perplexity with clear sections:

1. **Summary** - Brief overview of your response
2. **Market Intelligence** - Use the provided market data to give specific insights about salaries, companies, and trends
3. **Current Trends** - Use web search results to provide recent developments and industry insights
4. **Career Insights** - Key insights and actionable advice based on current market conditions
5. **Next Steps** - Specific, actionable steps the user can take

CRITICAL INSTRUCTIONS:
- You MUST incorporate the specific information from the web search results provided below
- Quote exact numbers, dates, company names, and specific details from the web search results
- Do NOT provide generic advice - use the current, specific information that was found through web search
- If web search results contain specific salary ranges, company names, or recent developments, you MUST include them in your response
- The web search results are the most current and accurate information available - prioritize this over general knowledge
- Be comprehensive and detailed - aim for 500-800 words with specific examples and data
- Use ALL the web search results provided, not just a summary"""

    # Build conversation context
    context = ""
    if conversation_history:
        context = "\n\nPrevious conversation:\n"
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            context += f"{msg.role}: {msg.content}\n"
    
    # Add market data context
    market_context = ""
    if market_data:
        market_context = "\n\nAvailable Market Data:\n"
        
        if market_data.get('top_companies'):
            market_context += f"Top companies hiring: {', '.join(market_data['top_companies'])}\n"
        
        if market_data.get('salary_insights'):
            salaries = market_data['salary_insights']
            if salaries:
                min_sal = min(s.get('min', 0) for s in salaries if s.get('min'))
                max_sal = max(s.get('max', 0) for s in salaries if s.get('max'))
                if min_sal and max_sal:
                    market_context += f"Salary range: ${min_sal:,} - ${max_sal:,}\n"
        
        if market_data.get('trending_industries'):
            market_context += f"Trending industries: {', '.join(market_data['trending_industries'])}\n"
    
    # Add web results context
    web_context = ""
    if web_results:
        web_context = "\n\n🔥 CURRENT WEB SEARCH RESULTS (MUST USE THESE IN YOUR RESPONSE):\n"
        web_context += "These are the most current and accurate details you MUST incorporate:\n\n"
        for i, result in enumerate(web_results, 1):
            if result.get('section'):
                web_context += f"RESULT {i} - {result['section']}: {result['content']}\n\n"
            else:
                web_context += f"RESULT {i}: {result['content']}\n\n"
        web_context += "REMEMBER: You MUST use the specific details, numbers, and information from these web search results in your response.\n"
    
    return f"{system_prompt}{market_context}\n\nUser's current question: {user_message}{context}\n\n{web_context}"

@router.post("/chat")
def chat_with_coach(request: ChatRequest):
    """Chat with career coach - Perplexity-style responses with market data"""
    
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        # Extract career terms and fetch data from multiple sources
        career_terms = extract_career_terms(request.message)
        print(f"Extracted career terms: {career_terms}")
        
        market_data = fetch_adzuna_market_data(career_terms)
        print(f"Market data fetched: {bool(market_data)}")
        
        web_results = fetch_perplexity_web_results(request.message)
        print(f"Web results fetched: {len(web_results)} results")
        
        # Generate enhanced prompt with both market data and web results
        prompt = get_career_coaching_prompt(request.message, request.conversation_history, market_data, web_results)
        
        # Debug: Print the prompt to see what's being sent to AI
        print(f"DEBUG - Web results being sent to AI: {len(web_results)} results")
        for i, result in enumerate(web_results[:2], 1):
            print(f"  {i}. {result.get('content', '')[:100]}...")
        
        # Debug: Print a sample of the prompt being sent to AI
        print(f"DEBUG - Prompt sample (last 500 chars): {prompt[-500:]}")
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": request.message}
            ],
            max_tokens=1200,  # Increased for richer responses
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        
        # Extract structured information (simple parsing)
        sources = []
        next_steps = []
        
        # Look for sources and next steps in the response
        lines = reply.split('\n')
        in_sources = False
        in_next_steps = False
        
        for line in lines:
            line = line.strip()
            if 'sources' in line.lower() or 'references' in line.lower():
                in_sources = True
                in_next_steps = False
                continue
            elif 'next steps' in line.lower() or 'action items' in line.lower():
                in_next_steps = True
                in_sources = False
                continue
            elif line.startswith('#') or line.startswith('**'):
                in_sources = False
                in_next_steps = False
                continue
            elif in_sources and line.startswith('-'):
                sources.append(line[1:].strip())
            elif in_next_steps and line.startswith('-'):
                next_steps.append(line[1:].strip())
        
        # Add market data sources
        if market_data.get('top_companies'):
            sources.append(f"Top hiring companies: {', '.join(market_data['top_companies'][:3])}")
        if market_data.get('salary_insights'):
            sources.append("Salary data from Adzuna job market")
        
        # Add web search sources
        if web_results:
            sources.append("Current web search results from Perplexity")
        
        return {
            "reply": reply,
            "sources": sources[:3],  # Limit to 3 sources
            "next_steps": next_steps[:3],  # Limit to 3 next steps
            "market_data": market_data,  # Include raw market data
            "web_results": web_results  # Include web search results
        }
        
    except Exception as e:
        # Fallback response when full integration fails due to architecture issues
        fallback_response = f"""I understand you're asking about: "{request.message}"

While I'm experiencing some technical issues with my full AI capabilities, I can still provide you with basic career guidance:

**Career Insights:**
• Focus on developing in-demand skills in your field
• Network actively with professionals in your industry
• Consider certifications or additional training
• Stay updated with industry trends and technologies

**Next Steps:**
• Research current job market trends for your field
• Update your resume and LinkedIn profile
• Practice your interview skills
• Consider reaching out to mentors or career coaches

I apologize for the limited response. The full AI-powered career coaching features will be available once the technical issues are resolved.

Would you like to try the job search feature instead? It's working perfectly and can help you find relevant opportunities."""
        
        return {
            "reply": fallback_response,
            "sources": ["Career guidance from Pathio", "Job market insights"],
            "next_steps": ["Try the job search feature", "Update your professional profiles", "Network with industry professionals"],
            "market_data": {},
            "web_results": []
        }

@router.get("/chat/health")
def chat_health():
    """Check if OpenAI and Perplexity are configured"""
    return {
        "openai_configured": bool(OPENAI_API_KEY),
        "perplexity_configured": bool(PERPLEXITY_API_KEY),
        "model": OPENAI_MODEL,
        "status": "healthy" if OPENAI_API_KEY else "missing_api_key"
    }
