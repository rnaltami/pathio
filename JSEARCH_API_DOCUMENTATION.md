# JSearch API Documentation

Complete reference documentation for the RapidAPI JSearch API. Includes code examples, data samples, and usage guides for delivering real-time job listings and salary data from public sources and Google for Jobs.

## Server
**Server:** `https://jsearch.p.rapidapi.com`

## Authentication
**Required**  
**Auth Type:** RapidAPI Key  
**API Key Name:** `X-RapidAPI-Key`  
**Host Header:** `X-RapidAPI-Host: jsearch.p.rapidapi.com`  
**Value:** [Your RapidAPI Key]

## Client Libraries
- Python `http.client`
- Python `requests` (recommended)

## Endpoints

### 1. Job Search
Search for jobs posted on any public job site across the web on the largest job aggregate in the world (Google for Jobs).

**Endpoint:** `GET /search`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Free-form jobs search query. Include job title and location for best results |
| `page` | integer | ❌ | 1 | Page to return (each page includes up to 10 results). Range: 1-100 |
| `num_pages` | integer | ❌ | 1 | Number of pages to return, starting from page. Range: 1-20 |
| `country` | string | ❌ | "us" | Country code (ISO 3166-1 alpha-2) |
| `language` | string | ❌ | - | Language code (ISO 639) |
| `date_posted` | string | ❌ | "all" | Time filter: "all", "today", "3days", "week", "month" |
| `work_from_home` | boolean | ❌ | false | Only return remote jobs |
| `employment_types` | string | ❌ | - | Comma-delimited: "FULLTIME", "CONTRACTOR", "PARTTIME", "INTERN" |
| `job_requirements` | string | ❌ | - | Comma-delimited: "under_3_years_experience", "more_than_3_years_experience", "no_experience", "no_degree" |
| `radius` | number | ❌ | - | Distance from location in km |
| `exclude_job_publishers` | string | ❌ | - | Comma-separated list of publishers to exclude |
| `fields` | string | ❌ | - | Comma-separated list of fields to include |

#### Example Request
```bash
curl 'https://jsearch.p.rapidapi.com/search?query=developer%20jobs%20in%20chicago&page=1&num_pages=3' \
  --header 'X-RapidAPI-Key: YOUR_RAPIDAPI_KEY' \
  --header 'X-RapidAPI-Host: jsearch.p.rapidapi.com'
```

#### Response Structure
```json
{
  "status": "OK",
  "request_id": "4f24fa29-a883-49f9-8dca-d0fede07203c",
  "parameters": {
    "query": "developer jobs in chicago",
    "page": 1,
    "num_pages": 1,
    "date_posted": "all",
    "country": "us",
    "language": "en"
  },
  "data": [
    {
      "job_id": "woj2gE2S_6LqvmLAAAAAAA==",
      "job_title": "Senior Developer",
      "employer_name": "United Airlines",
      "employer_logo": "https://encrypted-tbn0.gstatic.com/images/...",
      "employer_website": "https://www.united.com",
      "job_publisher": "United Airlines Jobs",
      "job_employment_type": "Full-time",
      "job_employment_types": ["FULLTIME"],
      "job_apply_link": "https://careers.united.com/us/en/job/...",
      "job_apply_is_direct": false,
      "apply_options": [...],
      "job_description": "Description...",
      "job_is_remote": false,
      "job_posted_at": "2 days ago",
      "job_posted_at_timestamp": 1743206400,
      "job_posted_at_datetime_utc": "2025-03-29T00:00:00.000Z",
      "job_location": "Chicago, IL",
      "job_city": "Chicago",
      "job_state": "Illinois",
      "job_country": "US",
      "job_latitude": 41.8781136,
      "job_longitude": -87.6297982,
      "job_benefits": ["dental_coverage", "paid_time_off", "health_insurance"],
      "job_google_link": "https://www.google.com/search?q=jobs&gl=us&hl=en&udm=8#vhid=...",
      "job_salary": null,
      "job_min_salary": null,
      "job_max_salary": null,
      "job_salary_period": null,
      "job_highlights": {
        "Qualifications": [...],
        "Benefits": [...],
        "Responsibilities": [...]
      },
      "job_onet_soc": "15113200",
      "job_onet_job_zone": "4"
    }
  ]
}
```

### 2. Job Details
Get all job details, including additional information such as application options/links, employer reviews and estimated salaries.

**Endpoint:** `GET /job-details`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `job_id` | string | ✅ | - | Job ID (supports batching up to 20 IDs with comma separation) |
| `country` | string | ❌ | "us" | Country code |
| `language` | string | ❌ | - | Language code |
| `fields` | string | ❌ | - | Comma-separated list of fields to include |

#### Example Request
```bash
curl 'https://jsearch.p.rapidapi.com/job-details?job_id=n20AgUu1KG0BGjzoAAAAAA%3D%3D' \
  --header 'X-RapidAPI-Key: YOUR_RAPIDAPI_KEY' \
  --header 'X-RapidAPI-Host: jsearch.p.rapidapi.com'
```

### 3. Job Salary
Get estimated salaries/pay for jobs around a location by job title and location.

**Endpoint:** `GET /estimated-salary`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `job_title` | string | ✅ | - | Job title for salary estimation |
| `location` | string | ✅ | - | Location for salary estimation |
| `location_type` | string | ❌ | "ANY" | Type: "ANY", "CITY", "STATE", "COUNTRY" |
| `years_of_experience` | string | ❌ | "ALL" | Experience level: "ALL", "LESS_THAN_ONE", "ONE_TO_THREE", "FOUR_TO_SIX", "SEVEN_TO_NINE", "TEN_TO_FOURTEEN", "ABOVE_FIFTEEN" |
| `fields` | string | ❌ | - | Comma-separated list of fields to include |

#### Example Request
```bash
curl 'https://jsearch.p.rapidapi.com/estimated-salary?job_title=nodejs%20developer&location=new%20york' \
  --header 'X-RapidAPI-Key: YOUR_RAPIDAPI_KEY' \
  --header 'X-RapidAPI-Host: jsearch.p.rapidapi.com'
```

### 4. Company Job Salary
Get estimated job salaries/pay in a specific company by job title and optionally a location and experience level.

**Endpoint:** `GET /company-job-salary`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | string | ✅ | - | Company name (e.g., "Amazon") |
| `job_title` | string | ✅ | - | Job title for salary estimation |
| `location` | string | ❌ | - | Free-text location/area |
| `location_type` | string | ❌ | "ANY" | Type: "ANY", "CITY", "STATE", "COUNTRY" |
| `years_of_experience` | string | ❌ | "ALL" | Experience level range |

#### Example Request
```bash
curl 'https://jsearch.p.rapidapi.com/company-job-salary?company=Amazon&job_title=software%20developer&location=NY' \
  --header 'X-RapidAPI-Key: YOUR_RAPIDAPI_KEY' \
  --header 'X-RapidAPI-Host: jsearch.p.rapidapi.com'
```

## Python Implementation Example

```python
import requests

def search_jobs(query, location=None, job_type=None, api_key=None):
    """Search for jobs using JSearch API"""
    
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    params = {
        "query": query,
        "page": 1,
        "num_pages": 3,
        "country": "us"
    }
    
    # Add location to query if provided
    if location:
        params["query"] = f"{query} in {location}"
    
    # Set remote work preference
    if job_type == "remote":
        params["work_from_home"] = True
    elif job_type in ["hybrid", "onsite"]:
        params["work_from_home"] = False
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"JSearch API error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching jobs from JSearch: {e}")
        return []
```

## Key Features

1. **Real-time Data**: Live job listings from Google for Jobs
2. **Comprehensive Filtering**: Extensive search and filter options
3. **Global Coverage**: Support for multiple countries and languages
4. **Salary Data**: Built-in salary estimation and company-specific data
5. **High Performance**: Fast response times with reliable uptime
## Rate Limits and Pricing

- Free tier: 100 requests per month
- Pro tier: 1,000 requests per month
- Enterprise: Custom pricing and limits
- Additional pages charged at 2x rate (2-10 pages) or 3x rate (10+ pages)

## Error Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **401**: Unauthorized (invalid API key)
- **422**: Unprocessable Entity (validation errors)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

## Notes

- All timestamps are in UTC
- Job IDs are unique and can be used for job details requests
- Results are paginated with up to 10 jobs per page
- Some fields may be null if not available from the job posting
- The API aggregates data from multiple job sites including Indeed, LinkedIn, Glassdoor, and others
