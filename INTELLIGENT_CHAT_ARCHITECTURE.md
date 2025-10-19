# Intelligent Chat Architecture

## Overview
This document describes the intelligent career coaching chatbot that combines OpenAI, Perplexity, and Adzuna APIs to provide comprehensive, real-time career guidance with citation-rich responses.

## Architecture

### Frontend (Next.js/TypeScript)
- **Location**: `/frontend-react/app/page.tsx`
- **Purpose**: Handles chat input/output rendering and user interaction
- **Key Features**:
  - Perplexity-style dark UI with centered search box
  - Real-time message display with structured formatting
  - Clickable source links for transparency
  - Market intelligence display from Adzuna data
  - Loading states and error handling

### Backend (FastAPI/Python)
- **Location**: `/backend/app/main.py`
- **Purpose**: Orchestrates three external APIs and synthesizes responses
- **Key Features**:
  - Parallel API calls using `asyncio.gather()`
  - Structured JSON output with sources and market data
  - Error handling and fallbacks for each API
  - Real-time data synthesis

## API Integration

### 1. Perplexity API
- **Purpose**: Real-time web search and current data
- **Model**: `sonar-pro`
- **Configuration**:
  ```python
  perplexity_client = openai.OpenAI(
      api_key=os.getenv("PERPLEXITY_API_KEY"),
      base_url="https://api.perplexity.ai"
  )
  ```
- **Parameters**:
  - `search_mode`: "web"
  - `search_recency_filter`: "month"
  - `max_results`: 10
- **Returns**: Web search results with titles, URLs, snippets, and dates

### 2. Adzuna API
- **Purpose**: Job market data and salary insights
- **Endpoint**: `https://api.adzuna.com/v1/api/jobs/us/search/1`
- **Configuration**:
  - `ADZUNA_APP_ID`: Your Adzuna application ID
  - `ADZUNA_APP_KEY`: Your Adzuna application key
- **Returns**: Job listings, salary ranges, and market statistics

### 3. OpenAI API
- **Purpose**: Intelligent reasoning and response synthesis
- **Model**: `gpt-4-turbo`
- **Configuration**:
  ```python
  openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
- **Role**: Synthesizes data from Perplexity and Adzuna into structured responses

## Data Flow

### 1. User Input
- User types question in chat interface
- Frontend sends POST request to `/api/chat`

### 2. Parallel API Calls
```python
# Run Perplexity and Adzuna in parallel
perplexity_task = asyncio.create_task(fetch_perplexity_web_results(request.message))
adzuna_task = asyncio.create_task(fetch_adzuna_market_data(request.message))

# Wait for both to complete
perplexity_data, adzuna_data = await asyncio.gather(perplexity_task, adzuna_task)
```

### 3. Data Synthesis
- Combine Perplexity web results with Adzuna market data
- Create comprehensive prompt for OpenAI
- Generate structured response with sections and bullet points

### 4. Response Format
```json
{
  "reply": "Structured AI response with sections and bullet points",
  "market_data": {
    "total_jobs": 150,
    "salary_info": {
      "min": 80000,
      "max": 150000
    }
  },
  "sources": [
    {
      "title": "Job Market Report 2025",
      "url": "https://example.com/report"
    }
  ],
  "web_results": [
    {
      "title": "Web Search Result",
      "url": "https://example.com",
      "snippet": "Relevant information...",
      "date": "2025-01-01"
    }
  ]
}
```

## Performance Optimization

### Parallel Processing
- Perplexity and Adzuna calls run simultaneously
- Total latency ≈ 3 seconds (vs 6+ seconds sequential)
- OpenAI synthesis happens after both data sources complete

### Caching Strategy
- Adzuna results can be cached for 15 minutes
- Perplexity results are always fresh (real-time)
- OpenAI responses can be cached based on query similarity

### Error Handling
- Each API has individual error handling
- Fallback responses when APIs fail
- Graceful degradation of features

## Environment Variables

### Required API Keys
```bash
OPENAI_API_KEY=your_openai_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here
```

### Backend Environment
- **Location**: `/backend/.env`
- **Python Version**: 3.11
- **Virtual Environment**: `/backend/.venv/`

### Frontend Environment
- **Location**: `/frontend-react/.env.local`
- **Node Version**: 18+
- **Package Manager**: npm

## Response Structure

### Frontend Display
1. **User Message**: Right-aligned purple bubble
2. **AI Response**: Left-aligned with structured formatting
   - Bold section headers
   - Bullet points with purple dots
   - Regular paragraphs
3. **Sources Section**: Clickable links at bottom
4. **Market Intelligence**: Salary and job data display

### Backend Processing
1. **Extract career terms** from user input
2. **Fetch parallel data** from Perplexity and Adzuna
3. **Synthesize insights** into structured format
4. **Generate response** with OpenAI
5. **Return structured JSON** with all data

## Key Features

### Real-time Data
- Web search results from Perplexity
- Current job market data from Adzuna
- Fresh, up-to-date information

### Citation Transparency
- All sources are clickable links
- URLs preserved from original APIs
- Clear attribution for all data

### Structured Responses
- Clear sections (Summary, Insights, Next Steps)
- Bullet points for easy scanning
- Market intelligence display

### Performance
- Parallel API calls for speed
- Error handling and fallbacks
- Responsive UI with loading states

## Troubleshooting

### Common Issues
1. **API Keys Missing**: Check `.env` file configuration
2. **Slow Responses**: Verify API key validity and network
3. **No Sources**: Check Perplexity API configuration
4. **No Market Data**: Verify Adzuna API keys and limits

### Debug Information
- Backend logs show API call status
- Frontend console shows response data
- Network tab shows API request/response timing

## Future Enhancements

### Planned Features
- Response streaming for better UX
- Conversation history persistence
- Advanced caching strategies
- Multi-language support
- Custom prompt templates

### Performance Improvements
- Response caching
- Background data refresh
- Optimized API call batching
- CDN for static assets
