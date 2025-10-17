from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Pathio Backend",
    description="Clean, simple backend for career and job search app",
    version="2.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://pathio-frontend.onrender.com",
        "https://pathio-c9yz.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from .routers import jobs, chat, tailor, adzuna

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(tailor.router, prefix="/api", tags=["tailor"])
app.include_router(adzuna.router, prefix="/api", tags=["adzuna"])

@app.get("/")
def root():
    return {
        "service": "Pathio Backend v2.0",
        "status": "running",
        "endpoints": [
            "/api/jobs/search",
            "/api/chat", 
            "/api/tailor/resume",
            "/api/tailor/cover-letter"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

