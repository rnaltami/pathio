# Pathio API Documentation

## Overview
Complete API documentation for all endpoints in the Pathio career platform.

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: TBD

## Authentication
Currently no authentication required. All endpoints are public.

## API Endpoints

### 1. Chat API

#### `POST /api/chat`
Intelligent chat with Perplexity + OpenAI + Adzuna integration.

**Request Body:**
```json
{
  "message": "string"
}
```

**Response:**
```json
{
  "reply": "string",
  "market_data": {
    "salary_info": {
      "min": "number",
      "max": "number"
    },
    "job_count": "number"
  },
  "sources": [
    {
      "title": "string",
      "url": "string"
    }
  ],
  "web_results": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string"
    }
  ]
}
```

**Features:**
- Smart filtering for conversational responses
- Real-time web search via Perplexity
- Market data integration via Adzuna
- Structured response formatting
- Source attribution

### 2. AI Tools API

#### `POST /api/ai-tools`
Direct OpenAI integration for AI tools recommendations.

**Request Body:**
```json
{
  "query": "string"
}
```

**Response:**
```json
{
  "response": "string"
}
```

**Features:**
- Direct OpenAI GPT-4 calls
- Specialized AI tools prompt
- Clean text formatting
- No markdown complexity

### 3. Job Search API

#### `POST /api/jobs/search`
Adzuna-powered job search with smart remote logic.

**Request Body:**
```json
{
  "query": "string",
  "location": "string" // optional
}
```

**Response:**
```json
{
  "jobs": [
    {
      "title": "string",
      "company": "string",
      "location": "string",
      "type": "string",
      "description": "string",
      "url": "string",
      "salary_min": "number",
      "salary_max": "number",
      "posted_at": "string"
    }
  ],
  "total": "number"
}
```

**Features:**
- Smart remote logic (no location = nationwide remote)
- Up to 50 results per page
- Salary information when available
- Clean job descriptions

### 4. Career Analytics API

#### `POST /api/analytics/upload`
Resume file upload with text extraction.

**Request Body:**
```
multipart/form-data
file: File
```

**Response:**
```json
{
  "text": "string",
  "filename": "string"
}
```

#### `POST /api/analytics/resume`
Comprehensive resume analysis with OpenAI.

**Request Body:**
```json
{
  "resume_text": "string"
}
```

**Response:**
```json
{
  "skills": ["string"],
  "career_level": "string",
  "experience_years": "number",
  "current_role": "string",
  "market_value": {
    "estimated_salary_min": "number",
    "estimated_salary_max": "number",
    "market_demand": "string",
    "growth_potential": "string"
  },
  "salary_insights": {
    "current_range": "string",
    "next_level_range": "string",
    "industry_average": "string"
  },
  "recommendations": ["string"],
  "skill_gaps": ["string"],
  "industry_insights": {
    "trending_skills": ["string"],
    "growth_areas": ["string"],
    "remote_opportunities": "string"
  }
}
```

### 5. Help Me Apply API

#### `POST /api/help-me-apply`
Job-resume matching analysis.

**Request Body:**
```json
{
  "jobDescription": "string",
  "resume": "string"
}
```

**Response:**
```json
{
  "jobTitle": "string",
  "matchScore": "number",
  "improvements": ["string"],
  "dailyTasks": ["string"],
  "canTailor": "boolean"
}
```

#### `POST /api/tailor-resume`
Resume customization for specific job.

**Request Body:**
```json
{
  "jobDescription": "string",
  "resume": "string"
}
```

**Response:**
```json
{
  "tailoredResume": "string"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Not Found
- **500**: Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message"
}
```

## Rate Limiting

Currently no rate limiting implemented. Consider implementing for production.

## Environment Variables

Required environment variables:

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_key

# Perplexity API
PERPLEXITY_API_KEY=your_perplexity_key

# Adzuna API
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

## CORS Configuration

CORS is configured for:
- `http://localhost:3000` (Next.js dev server)
- `http://localhost:3001` (Alternative port)

## API Usage Examples

### Chat Example
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top tech companies to work for?"}'
```

### Job Search Example
```bash
curl -X POST http://localhost:8000/api/jobs/search \
  -H "Content-Type: application/json" \
  -d '{"query": "software engineer", "location": "San Francisco"}'
```

### AI Tools Example
```bash
curl -X POST http://localhost:8000/api/ai-tools \
  -H "Content-Type: application/json" \
  -d '{"query": "video editing tools"}'
```

### Career Analytics Example
```bash
curl -X POST http://localhost:8000/api/analytics/resume \
  -H "Content-Type: application/json" \
  -d '{"resume_text": "John Doe\nSoftware Engineer\n5 years experience..."}'
```

## Response Times

Typical response times:
- **Chat**: 3-5 seconds (Perplexity + OpenAI + Adzuna)
- **AI Tools**: 2-3 seconds (OpenAI only)
- **Job Search**: 1-2 seconds (Adzuna)
- **Career Analytics**: 3-4 seconds (OpenAI)
- **Help Me Apply**: 4-6 seconds (OpenAI analysis + tailoring)

## Future Enhancements

- **Authentication**: User accounts and session management
- **Rate Limiting**: Prevent API abuse
- **Caching**: Improve response times
- **Webhooks**: Real-time updates
- **Analytics**: Usage tracking and insights
- **Versioning**: API version management
