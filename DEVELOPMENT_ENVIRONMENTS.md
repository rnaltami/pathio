# Development Environments Guide

## Backend Environment

### Location
- **Path**: `/Users/roxana/CodingProjects/pathio/backend/`
- **Virtual Environment**: `/Users/roxana/CodingProjects/pathio/backend/.venv/`

### Setup Commands
```bash
# Navigate to backend
cd /Users/roxana/CodingProjects/pathio/backend

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python3 -m uvicorn app.main:app --reload --port 8000
```

### Key Files
- **Main App**: `app/main.py`
- **Environment**: `app/.env` (create if missing)
- **Dependencies**: `requirements.txt`
- **Virtual Env**: `.venv/` (already exists)

### Environment Variables (Backend)
Create `/Users/roxana/CodingProjects/pathio/backend/app/.env`:
```bash
OPENAI_API_KEY=your_openai_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here
```

### Common Issues & Solutions

#### 1. "Address already in use" Error
```bash
# Kill existing process
pkill -f uvicorn

# Or find and kill specific port
lsof -ti:8000 | xargs kill -9
```

#### 2. "ModuleNotFoundError" for aiohttp
```bash
cd /Users/roxana/CodingProjects/pathio/backend
source .venv/bin/activate
pip install aiohttp
```

#### 3. Architecture Mismatch (ARM64 vs x86_64)
```bash
# Use the existing .venv (it works)
cd /Users/roxana/CodingProjects/pathio/backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --port 8000
```

#### 4. API Keys Not Loading
- Check `app/.env` file exists
- Verify `load_dotenv()` is called in `main.py`
- Restart the server after adding keys

## Frontend Environment

### Location
- **Path**: `/Users/roxana/CodingProjects/pathio/frontend-react/`
- **Node Modules**: `/Users/roxana/CodingProjects/pathio/frontend-react/node_modules/`

### Setup Commands
```bash
# Navigate to frontend
cd /Users/roxana/CodingProjects/pathio/frontend-react

# Install dependencies
npm install

# Start development server
npm run dev
```

### Key Files
- **Main Page**: `app/page.tsx`
- **Layout**: `app/layout.tsx`
- **Package Config**: `package.json`
- **Next Config**: `next.config.js`

### Environment Variables (Frontend)
Create `/Users/roxana/CodingProjects/pathio/frontend-react/.env.local`:
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Common Issues & Solutions

#### 1. "Port 3000 is in use"
- Frontend automatically tries port 3001
- Access at `http://localhost:3001`

#### 2. "Fast Refresh had to perform a full reload"
- This is normal during development
- Usually resolves automatically

#### 3. "Invalid next.config.js options"
- Warning about `appDir` in experimental
- Can be ignored or fixed by updating config

#### 4. Webpack Cache Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

## Development Workflow

### Starting Both Services

#### Terminal 1 (Backend)
```bash
cd /Users/roxana/CodingProjects/pathio/backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --port 8000
```

#### Terminal 2 (Frontend)
```bash
cd /Users/roxana/CodingProjects/pathio/frontend-react
npm run dev
```

### Access Points
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Testing the Chat
1. Go to http://localhost:3001
2. Select "Chat" tab
3. Type: "How can I get a job at Discord?"
4. Press Enter or click "Ask AI"
5. Check browser console for response logs

## File Structure

```
/Users/roxana/CodingProjects/pathio/
├── backend/
│   ├── .venv/                    # Python virtual environment
│   ├── app/
│   │   ├── main.py              # Main FastAPI application
│   │   └── .env                 # Backend environment variables
│   └── requirements.txt         # Python dependencies
├── frontend-react/
│   ├── node_modules/            # Node.js dependencies
│   ├── app/
│   │   ├── page.tsx            # Main page component
│   │   └── layout.tsx          # Root layout
│   ├── package.json            # Node.js dependencies
│   └── .env.local              # Frontend environment variables
└── INTELLIGENT_CHAT_ARCHITECTURE.md
```

## Quick Commands Reference

### Backend
```bash
# Start backend
cd /Users/roxana/CodingProjects/pathio/backend && source .venv/bin/activate && python3 -m uvicorn app.main:app --reload --port 8000

# Test backend
curl http://localhost:8000/

# Test chat API
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message": "test"}'
```

### Frontend
```bash
# Start frontend
cd /Users/roxana/CodingProjects/pathio/frontend-react && npm run dev

# Install new package
npm install package-name

# Clear cache
rm -rf .next && npm run dev
```

### Both
```bash
# Kill all processes
pkill -f uvicorn
pkill -f next

# Restart everything
# Terminal 1: Backend command above
# Terminal 2: Frontend command above
```

## Troubleshooting Checklist

### Backend Issues
- [ ] Virtual environment activated?
- [ ] API keys in `app/.env`?
- [ ] Port 8000 available?
- [ ] Dependencies installed?
- [ ] Server logs showing errors?

### Frontend Issues
- [ ] Node modules installed?
- [ ] Port 3001 accessible?
- [ ] Backend running on 8000?
- [ ] Browser console showing errors?
- [ ] Network requests failing?

### Integration Issues
- [ ] CORS configured correctly?
- [ ] API endpoints responding?
- [ ] Environment variables loaded?
- [ ] Network connectivity working?

## Success Indicators

### Backend Working
- Server starts without errors
- `http://localhost:8000/` returns JSON
- `http://localhost:8000/docs` shows API docs
- Chat endpoint responds to POST requests

### Frontend Working
- Page loads at `http://localhost:3001`
- Chat interface displays
- No console errors
- API calls succeed

### Full System Working
- Chat responses appear in UI
- Sources are clickable
- Market data displays
- No timeout errors

