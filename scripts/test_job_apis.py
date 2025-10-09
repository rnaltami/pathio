#!/usr/bin/env python3
"""
Test script to evaluate different job API options
Run this to see what data quality/quantity we can get
"""

import requests
import json
from datetime import datetime

def test_remoteok_rss():
    """Test RemoteOK RSS feed (no API key needed)"""
    print("\n" + "="*60)
    print("Testing RemoteOK RSS Feed")
    print("="*60)
    
    try:
        # RemoteOK has a public API
        url = "https://remoteok.com/api"
        headers = {'User-Agent': 'Pathio Job Aggregator Test'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            jobs = response.json()
            # First item is metadata, rest are jobs
            actual_jobs = jobs[1:] if len(jobs) > 1 else []
            
            print(f"✓ Status: SUCCESS")
            print(f"✓ Total Jobs Found: {len(actual_jobs)}")
            print(f"✓ API Key Required: NO")
            print(f"✓ Rate Limit: Unknown (be conservative)")
            
            if actual_jobs:
                print(f"\n--- Sample Job ---")
                sample = actual_jobs[0]
                print(f"Title: {sample.get('position', 'N/A')}")
                print(f"Company: {sample.get('company', 'N/A')}")
                print(f"Location: {sample.get('location', 'N/A')}")
                print(f"Tags: {', '.join(sample.get('tags', [])[:5])}")
                print(f"Salary: {sample.get('salary', 'Not specified')}")
                print(f"URL: {sample.get('url', 'N/A')}")
                
                # Check data completeness
                complete_jobs = sum(1 for j in actual_jobs[:50] if j.get('position') and j.get('company'))
                print(f"\nData Quality: {complete_jobs}/50 jobs have complete basic info")
            
            return len(actual_jobs)
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 0


def test_usajobs_api():
    """Test USAJobs API (free, no key needed for basic search)"""
    print("\n" + "="*60)
    print("Testing USAJobs API (Government Jobs)")
    print("="*60)
    
    try:
        url = "https://data.usajobs.gov/api/search"
        params = {
            'Keyword': 'software engineer',
            'ResultsPerPage': 50
        }
        # USAJobs requires email in User-Agent
        headers = {
            'User-Agent': 'pathio-test@example.com',
            'Host': 'data.usajobs.gov'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('SearchResult', {}).get('SearchResultItems', [])
            
            print(f"✓ Status: SUCCESS")
            print(f"✓ Total Jobs Found: {len(jobs)}")
            print(f"✓ API Key Required: NO (basic) / YES (advanced)")
            print(f"✓ Rate Limit: Generous")
            
            if jobs:
                print(f"\n--- Sample Job ---")
                job_data = jobs[0].get('MatchedObjectDescriptor', {})
                print(f"Title: {job_data.get('PositionTitle', 'N/A')}")
                print(f"Agency: {job_data.get('OrganizationName', 'N/A')}")
                print(f"Location: {job_data.get('PositionLocationDisplay', 'N/A')}")
                print(f"Salary: {job_data.get('PositionRemuneration', [{}])[0].get('Description', 'N/A')}")
            
            return len(jobs)
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return 0
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 0


def test_github_jobs():
    """Test GitHub Jobs API status"""
    print("\n" + "="*60)
    print("Testing GitHub Jobs API")
    print("="*60)
    
    try:
        url = "https://jobs.github.com/positions.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"✓ Status: SUCCESS")
            print(f"✓ Total Jobs Found: {len(jobs)}")
            return len(jobs)
        else:
            print(f"✗ GitHub Jobs was shut down in 2021")
            print(f"Status: DEPRECATED")
            return 0
            
    except Exception as e:
        print(f"✗ Status: DEPRECATED (GitHub Jobs shut down)")
        return 0


def test_arbeitnow():
    """Test Arbeitnow API (free job board API)"""
    print("\n" + "="*60)
    print("Testing Arbeitnow API (Europe/Remote)")
    print("="*60)
    
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('data', [])
            
            print(f"✓ Status: SUCCESS")
            print(f"✓ Total Jobs Found: {len(jobs)}")
            print(f"✓ API Key Required: NO")
            print(f"✓ Rate Limit: Reasonable")
            
            if jobs:
                print(f"\n--- Sample Job ---")
                sample = jobs[0]
                print(f"Title: {sample.get('title', 'N/A')}")
                print(f"Company: {sample.get('company_name', 'N/A')}")
                print(f"Location: {sample.get('location', 'N/A')}")
                print(f"Tags: {', '.join(sample.get('tags', [])[:5])}")
                print(f"URL: {sample.get('url', 'N/A')}")
            
            return len(jobs)
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 0


def test_themuse():
    """Test TheMuse API (requires API key but has free tier)"""
    print("\n" + "="*60)
    print("Testing TheMuse API")
    print("="*60)
    
    try:
        # TheMuse has a public API endpoint without key for basic search
        url = "https://www.themuse.com/api/public/jobs"
        params = {
            'page': 1,
            'descending': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('results', [])
            total = data.get('page_count', 0) * len(jobs) if jobs else 0
            
            print(f"✓ Status: SUCCESS")
            print(f"✓ Jobs on this page: {len(jobs)}")
            print(f"✓ Estimated total: {total}+")
            print(f"✓ API Key Required: NO (public endpoint)")
            print(f"✓ Rate Limit: Unknown")
            
            if jobs:
                print(f"\n--- Sample Job ---")
                sample = jobs[0]
                print(f"Title: {sample.get('name', 'N/A')}")
                company = sample.get('company', {})
                print(f"Company: {company.get('name', 'N/A')}")
                locations = sample.get('locations', [])
                print(f"Location: {locations[0].get('name', 'N/A') if locations else 'N/A'}")
                print(f"Publication Date: {sample.get('publication_date', 'N/A')}")
            
            return len(jobs)
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 0


def main():
    print("\n" + "="*60)
    print("JOB API QUALITY TEST")
    print("Testing free/public job APIs to evaluate data quality")
    print("="*60)
    
    results = {}
    
    # Test each API
    results['RemoteOK'] = test_remoteok_rss()
    results['USAJobs'] = test_usajobs_api()
    results['Arbeitnow'] = test_arbeitnow()
    results['TheMuse'] = test_themuse()
    results['GitHub Jobs'] = test_github_jobs()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total_jobs = sum(v for v in results.values() if v > 0)
    working_apis = sum(1 for v in results.values() if v > 0)
    
    print(f"\nWorking APIs: {working_apis}/5")
    print(f"Total Jobs Found (single query): {total_jobs}")
    
    print("\n--- Recommendations ---")
    if results.get('RemoteOK', 0) > 0:
        print("✓ RemoteOK: Good for remote/tech jobs, no API key needed")
    if results.get('TheMuse', 0) > 0:
        print("✓ TheMuse: Good variety, no API key for basic use")
    if results.get('Arbeitnow', 0) > 0:
        print("✓ Arbeitnow: Good for Europe/remote, no API key needed")
    
    print("\n--- Next Steps ---")
    if total_jobs > 100:
        print("✓ We have enough data to build an MVP!")
        print("✓ Can combine multiple free sources for diversity")
    elif total_jobs > 50:
        print("~ Moderate data available")
        print("~ Consider combining with manual curation")
    else:
        print("✗ Limited free data available")
        print("✗ May need paid API tier or alternative approach")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()

