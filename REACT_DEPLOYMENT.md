# Pathio React Frontend - Deployment Guide

## Live URLs
- **Frontend:** https://pathio-frontend.onrender.com
- **Backend:** https://pathio-c9yz.onrender.com

## Features Built

### 1. Job Search (Homepage)
- Clean Perplexity-style UI
- Real job search powered by JSearch API ($25/month subscription)
- Smart filtering: Remote, Full-time, Contract, Location
- Inline job details (accordion expansion)
- Blue job titles, left-aligned

### 2. Application Preparation (`/apply`)
- Job description pre-filled from search results
- Resume paste field
- AI-powered resume tailoring
- Cover letter generation

### 3. Results Page (`/results`)
- 4 tabs: Tailored Resume, Cover Letter, What Changed, How to Stand Out
- Download buttons for .docx export
- Interactive action items with checkboxes
- "Show me how →" links to AI coaching

### 4. AI Career Coach (`/chat`)
- Task-specific guidance
- General career advice
- Conversational interface

## Technical Stack
- **Frontend:** Next.js 15 + React + TypeScript + Tailwind CSS
- **Backend:** FastAPI + Python
- **AI:** OpenAI GPT-4
- **Jobs API:** JSearch (RapidAPI)
- **Deployment:** Render

## Environment Variables

### Backend (pathio-c9yz)
```
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o
JSEARCH_API_KEY=3284d8ef3amsh...
ALLOWED_ORIGINS=https://pathio.streamlit.app,http://localhost:8501,http://localhost:3000,http://localhost:3001,https://pathio-frontend.onrender.com
```

### Frontend (pathio-frontend)
```
NEXT_PUBLIC_API_URL=https://pathio-c9yz.onrender.com
```

## Render Configuration

### Frontend Service
- **Root Directory:** `frontend-react`
- **Build Command:** `npm install && npm run build`
- **Start Command:** `npm start`
- **Environment:** Node

### Backend Service
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment:** Python 3.11

## Local Development

### Start Backend
```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend-react
npm run dev
```

Frontend will be at http://localhost:3000 (or 3001 if 3000 is occupied)

## Next Steps (Future Features)

### Premium Features (Not Yet Built)
- User authentication
- Resume version history
- Progress tracking across devices
- Skill evolution over time
- Application tracking
- Payment integration (Stripe)

### Free Tier Strategy
- Job search ✅
- Resume tailoring ✅
- Cover letter generation ✅
- Action items ✅
- AI coaching ✅

### Premium Upsell
- Save resumes forever
- Track progress on action items
- Auto-update resume as skills are learned
- Career path planning
- Application success analytics

## Known Issues to Address
- Markdown formatting (`###`, `**`) stripped in display but still in downloaded docs
- Action item skill extraction needs improvement for non-skill tasks
- "Job-Specific Highlights" section could be renamed or improved

## Success Metrics to Track
- Job searches per day
- Resume tailoring completions
- Action item engagement
- AI chat usage
- Download rate
- Return visitors (localStorage tracking)

