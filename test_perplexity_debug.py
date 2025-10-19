#!/usr/bin/env python3
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_perplexity_api():
    """Test Perplexity API to see actual response structure"""
    
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    
    if not PERPLEXITY_API_KEY:
        print("ERROR: PERPLEXITY_API_KEY not found in environment")
        return
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a career research assistant. Provide current, accurate information about job markets, salaries, and career trends. Focus on recent data and specific insights."
            },
            {
                "role": "user",
                "content": "Find recent career trends and insights about: What is the top trending job in 2025? Include salary data, job market trends, and industry developments."
            }
        ],
        "max_tokens": 800,
        "temperature": 0.1,
        "extra_body": {
            "search_mode": "pro",
            "search_focus": "academic",
            "max_results": 15,
            "search_recency_filter": "6months"
        }
    }
    
    print("Making request to Perplexity API...")
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print("\n=== FULL PERPLEXITY API RESPONSE ===")
        print(json.dumps(data, indent=2))
        
        print("\n=== SEARCH RESULTS ===")
        search_results = data.get("search_results", [])
        print(f"Count: {len(search_results)}")
        for i, result in enumerate(search_results[:3], 1):
            print(f"Result {i}: {result}")
        
        print("\n=== CITATIONS ===")
        citations = data.get("choices", [{}])[0].get("message", {}).get("citations", [])
        print(f"Count: {len(citations)}")
        for i, citation in enumerate(citations[:3], 1):
            print(f"Citation {i}: {citation}")
            
    else:
        print(f"ERROR: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_perplexity_api()