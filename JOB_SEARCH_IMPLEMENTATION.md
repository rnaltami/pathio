# Job Search Implementation - Adzuna API

## Overview
The job search functionality uses the Adzuna API to fetch job listings. This document outlines the current implementation and key learnings.

## Current Working Implementation

### Backend (`/backend/app/routers/jobs.py`)
- **API Endpoint**: `https://api.adzuna.com/v1/api/jobs/us/search/1`
- **Method**: GET request with query parameters
- **Results**: Up to 50 jobs per search (using `results_per_page: 50`)

### Key Parameters
```python
params = {
    "app_id": ADZUNA_APP_ID,           # From environment variables
    "app_key": ADZUNA_API_KEY,         # From environment variables  
    "what": request.query,             # Job title/keywords
    "results_per_page": 50,            # Maximum results per page
    "where": request.location          # Location (optional)
}

# Smart Remote Logic:
if request.location:
    params["where"] = request.location
else:
    # If no location provided, search for remote jobs
    params["what"] = request.query + " remote"
```

### Response Structure
Adzuna returns jobs in `data.results[]` with this structure:
```json
{
  "results": [
    {
      "title": "Job Title",
      "company": {"display_name": "Company Name"},
      "location": {"display_name": "City, State"},
      "contract_type": "Full Time",
      "description": "Job description...",
      "redirect_url": "https://...",
      "salary_min": 50000,
      "salary_max": 70000,
      "created": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## What Works ✅

### Simple API Call
- Single API request (no pagination)
- Basic parameters: `what`, `where`, `results_per_page`
- Clean error handling
- Up to 50 results per search

### Smart Remote Logic
- **With location**: Searches in specified location
- **Without location**: Automatically searches for remote jobs nationwide
- **User-friendly**: No need for separate remote filter

### Frontend Integration
- Simple form with job title and location fields
- Clean job cards display
- Company names in purple for better visibility
- Simple sorting by date or salary
- No complex filtering - just clean, intuitive search

## What Doesn't Work ❌

### Pagination
- **Issue**: Multiple page requests break the API call
- **Symptom**: Returns 400 errors with HTML error pages
- **Solution**: Use `results_per_page: 50` instead of pagination

### Complex Filtering
- **Issue**: Complex filtering was confusing and unreliable
- **Current State**: Removed complex filters, kept simple sorting only
- **Solution**: Smart remote logic handles remote jobs automatically

### Complex Parameters
- **Issue**: Adding extra parameters like `content-type`, `telecommuting` causes 400 errors
- **Solution**: Keep parameters minimal and basic

## Environment Setup

### Required Environment Variables
```bash
# In /backend/.env
ADZUNA_APP_ID=your_app_id_here
ADZUNA_API_KEY=your_api_key_here
```

### API Key Configuration
- Keys are loaded from `.env` file in backend directory
- Health endpoint at `/api/jobs/health` verifies configuration
- Keys must be valid and active

## API Limitations

### Rate Limits
- Adzuna has rate limits (typically 25 requests/minute)
- Current implementation makes 1 request per search
- No rate limiting implemented in our code

### Result Limits
- Maximum 50 results per page (tested and working)
- No reliable way to get more results via pagination
- Location filtering works but may reduce result count

### Data Quality
- Some jobs may have missing fields (salary, location, etc.)
- Job descriptions can be very long
- Company names and locations are generally reliable

## Frontend Implementation

### Job Search Page (`/frontend-react/app/job-search/page.tsx`)
- **Form**: Job title input + location input + search button
- **Results**: Clean job cards with company, location, salary, description
- **Styling**: Purple company names, conditional job type display
- **Navigation**: Click job card to view details
- **Sorting**: Simple sort by date (newest first) or salary (highest first)
- **Remote Logic**: Leave location blank to search for remote jobs

### Job Data Structure
```typescript
interface Job {
  title: string
  company: string
  location: string
  type: string
  description: string
  url: string
  salary_min?: number
  salary_max?: number
  posted_at?: string
}
```

## Troubleshooting

### Common Issues

1. **400 Error with HTML Response**
   - **Cause**: Invalid parameters or API endpoint
   - **Solution**: Use basic parameters only, check endpoint URL

2. **0 Jobs Returned**
   - **Cause**: API keys invalid or search too specific
   - **Solution**: Test with broader search terms, verify API keys

3. **Location Bias**
   - **Cause**: Adzuna may prioritize certain locations
   - **Solution**: Try searches without location to get global results

### Debug Information
The backend logs show:
- Search parameters being sent
- Number of jobs found
- API response status
- Error messages if API calls fail

## Future Improvements

### Potential Enhancements
1. **Search result caching** for faster repeated searches
2. **Better error messages** for users
3. **Search history** for recent searches
4. **Job alerts** for saved searches
5. **Company filtering** by specific companies
6. **Salary range filtering** with min/max inputs

### Alternative APIs
If Adzuna becomes unreliable:
- **JSearch API** (RapidAPI) - was previously used but had location bias issues
- **Indeed API** - if available
- **LinkedIn API** - for professional jobs
- **Multiple API aggregation** - combine results from different sources

## Key Learnings

1. **Keep it simple** - Basic API calls work better than complex implementations
2. **Test incrementally** - Small changes are easier to debug
3. **Environment variables** - API keys must be properly configured
4. **Error handling** - Always handle API failures gracefully
5. **User experience** - 50 results is better than complex pagination that breaks
6. **Smart defaults** - Auto-remote search when no location provided is intuitive
7. **Simple sorting** - Date and salary sorting is more useful than complex filters

## Current Status
✅ **Working**: Basic job search with up to 50 results  
✅ **Working**: Location-based filtering  
✅ **Working**: Smart remote job search (no location = remote)  
✅ **Working**: Simple sorting by date and salary  
✅ **Working**: Clean frontend display  
❌ **Not Working**: Pagination for more results  
❌ **Not Working**: Complex search parameters  

The implementation is stable and functional for basic job searching needs with intuitive remote job handling.
