# Pathio Development Setup

## Current Status ✅

### What's Working:
- ✅ **Backend**: Running on `http://localhost:8000` using `backend/.venv`
- ✅ **Frontend**: Running on `http://localhost:3000` 
- ✅ **Job Search API**: Fully functional with JSearch integration
- ✅ **Health Endpoints**: All responding correctly
- ✅ **Perplexity-style UI**: Clean, scannable responses implemented
- ✅ **All 5 Tabs**: Chat, Find Job, Help Me Apply, My Career Analytics, AI Tools

### What Needs Fixing:
- ⚠️ **Chat API**: Architecture mismatch with `jiter` package (ARM64 vs x86_64)
- ⚠️ **Deployed Backend**: Needs to be updated with latest code

## Quick Start Commands

### Start Backend:
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Start Frontend:
```bash
cd frontend-react
npm run dev
```

### Access Application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Working Features

### 1. Job Search
- **Endpoint**: `POST /api/jobs/search`
- **Format**: `{"query": "software engineer", "location": "San Francisco", "filter_type": "remote"}`
- **Status**: ✅ Working perfectly

### 2. Landing Page
- **Dynamic placeholders** for all 5 tabs
- **Location fields** for job search
- **Upload mechanism** for career analytics
- **Perplexity-style formatting** for chat responses
- **Global header** with Pathio logo navigation

### 3. UI/UX Features
- **Clean, scannable responses** with bold titles
- **Bullet points** and structured content
- **Source links** at the bottom
- **Responsive design** for mobile/desktop
- **Enter key submission** for all forms

## Architecture Issues

### Local Chat API Problem:
The chat endpoint fails with:
```
ImportError: dlopen(...jiter.cpython-311-darwin.so, 0x0002): 
incompatible architecture (have 'arm64', need 'x86_64')
```

### Solutions:
1. **Use deployed backend** for chat functionality
2. **Fix local architecture** by recreating virtual environment
3. **Use system Python** instead of framework Python

## Next Steps

1. **Test the application** at http://localhost:3000
2. **Verify job search** functionality
3. **Test UI/UX** features
4. **Deploy latest backend** to Render
5. **Fix local chat API** architecture issue

## Environment Variables Required

### Backend (.env in backend/):
```
JSEARCH_API_KEY=your_jsearch_key
OPENAI_API_KEY=your_openai_key
PERPLEXITY_API_KEY=your_perplexity_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_API_KEY=your_adzuna_api_key
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Frontend:
- No environment variables needed (uses backend API)

## Troubleshooting

### Backend Won't Start:
1. Check if port 8000 is free: `lsof -i :8000`
2. Kill existing processes: `pkill -f uvicorn`
3. Use the working command: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`

### Frontend Won't Start:
1. Check if port 3000 is free: `lsof -i :3000`
2. Kill existing processes: `pkill -f "next dev"`
3. Clear cache: `rm -rf .next && npm run dev`

### Chat API Issues:
- Use deployed backend temporarily
- Or fix local architecture issue
