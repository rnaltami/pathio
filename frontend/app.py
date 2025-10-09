# app_v2.py — Perplexity-inspired Pathio
# Clean, conversational job search and career coaching platform

import os
import json
import hashlib
import requests
import streamlit as st
from urllib.parse import quote, unquote
from datetime import datetime

# =========================
# Backend Configuration
# =========================
DEFAULT_BACKEND = "https://pathio-c9yz.onrender.com"
backend_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND).rstrip("/")

# Warm backend
try:
    requests.get(f"{backend_url}/healthz", timeout=3)
except Exception:
    pass

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Pathio - AI Career Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# Perplexity-Inspired Styling
# =========================
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    
    /* Global styles */
    :root {
        --bg-primary: #0A0A0A;
        --bg-secondary: #151515;
        --bg-tertiary: #1F1F1F;
        --text-primary: #ECECEC;
        --text-secondary: #B4B4B4;
        --text-tertiary: #6B6B6B;
        --accent-primary: #3B82F6;
        --accent-hover: #2563EB;
        --border-color: #2A2A2A;
        --input-bg: #1A1A1A;
    }
    
    /* Override Streamlit's default background */
    .main, .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .block-container {
        max-width: 900px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }
    
    /* Custom text styles */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: var(--text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    
    /* Header/Brand */
    .pathio-header {
        text-align: center;
        margin-bottom: 3rem;
        animation: fadeIn 0.6s ease-in;
    }
    
    .pathio-logo {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .pathio-tagline {
        font-size: 1.1rem;
        color: var(--text-secondary);
        font-weight: 400;
    }
    
    /* Search box - Perplexity style */
    .search-container {
        position: relative;
        margin: 2rem auto;
        max-width: 700px;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--input-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        padding: 1rem 1.25rem !important;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-tertiary) !important;
    }
    
    /* Buttons - clean and minimal */
    .stButton > button {
        background-color: var(--accent-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-hover) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Secondary button style */
    .secondary-btn button {
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .secondary-btn button:hover {
        background-color: var(--bg-secondary) !important;
        transform: translateY(-1px);
    }
    
    /* Cards/Containers */
    .job-card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .job-card:hover {
        border-color: var(--accent-primary);
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Dividers */
    hr {
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 2rem 0;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Quick actions */
    .quick-action {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .quick-action:hover {
        border-color: var(--accent-primary);
        background-color: var(--bg-tertiary);
    }
    
    /* Progress indicator */
    .progress-step {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: var(--bg-tertiary);
        border-radius: 20px;
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-right: 0.5rem;
    }
    
    .progress-step.active {
        background-color: var(--accent-primary);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# Session State
# =========================
st.session_state.setdefault("user_resume", "")
st.session_state.setdefault("current_step", "landing")  # landing, search, chat, job_detail, prepare, apply
st.session_state.setdefault("selected_job", None)
st.session_state.setdefault("search_query", "")
st.session_state.setdefault("search_results", [])
st.session_state.setdefault("chat_history", [])

# =========================
# Helper Functions
# =========================

def search_jobs(query: str, user_resume: str = None):
    """Search jobs using backend API"""
    try:
        response = requests.post(
            f"{backend_url}/search-jobs",
            json={
                "job_title": query,
                "user_resume": user_resume
            },
            timeout=15
        )
        if response.status_code == 200:
            return response.json().get("jobs", [])
    except Exception as e:
        st.error(f"Search failed: {e}")
    return []

def career_chat(user_message: str, history: list):
    """Career exploration chat"""
    try:
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": user_message})
        
        response = requests.post(
            f"{backend_url}/coach",
            json={"messages": messages},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("reply", "")
    except Exception:
        pass
    return "I'm here to help you explore career options. What kind of work interests you?"

# =========================
# UI Components
# =========================

def render_header():
    """Render the Pathio header"""
    st.markdown("""
        <div class="pathio-header fade-in">
            <div class="pathio-logo">pathio</div>
            <div class="pathio-tagline">Your AI-powered career assistant</div>
        </div>
    """, unsafe_allow_html=True)

def render_landing():
    """Landing page - main search interface"""
    render_header()
    
    # Main search box
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    search_query = st.text_input(
        "search",
        placeholder="What kind of job are you looking for?",
        label_visibility="collapsed",
        key="main_search"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search Jobs", use_container_width=True):
            if search_query:
                st.session_state["search_query"] = search_query
                st.session_state["current_step"] = "search"
                st.rerun()
    
    with col2:
        if st.button("💬 Not Sure? Chat with AI", use_container_width=True, key="chat_btn"):
            st.session_state["current_step"] = "chat"
            st.rerun()
    
    with col3:
        if st.button("📄 Have Resume? Upload", use_container_width=True, key="upload_btn"):
            st.session_state["show_resume_upload"] = True
            st.rerun()
    
    # Resume upload section
    if st.session_state.get("show_resume_upload", False):
        st.markdown("---")
        st.markdown("### 📄 Upload or Paste Your Resume")
        resume_text = st.text_area(
            "resume",
            placeholder="Paste your resume here to get personalized job matches...",
            height=200,
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Save Resume"):
                st.session_state["user_resume"] = resume_text
                st.session_state["show_resume_upload"] = False
                st.success("Resume saved! Now search for jobs to see personalized matches.")
                st.rerun()
        with col2:
            if st.button("Cancel", key="cancel_resume"):
                st.session_state["show_resume_upload"] = False
                st.rerun()

def render_search_results():
    """Display job search results"""
    query = st.session_state.get("search_query", "")
    
    # Header with back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "landing"
            st.rerun()
    
    st.markdown(f"### Results for: {query}")
    
    # Search results
    with st.spinner("Finding jobs..."):
        results = search_jobs(query, st.session_state.get("user_resume"))
        
    if not results:
        st.info("No jobs found. Try a different search term.")
        return
    
    st.markdown(f"Found {len(results)} jobs")
    
    for idx, job in enumerate(results):
        with st.container():
            st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0 0 0.5rem 0; font-size: 1.25rem;">{job.get('title', 'Job Title')}</h3>
                    <p style="margin:0; color: var(--text-secondary);">
                        {job.get('company', 'Company')} • {job.get('location', 'Location')}
                    </p>
                    <p style="margin:0.5rem 0; color: var(--text-tertiary); font-size: 0.9rem;">
                        Match: {job.get('match_score', 0)}%
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("View Details", key=f"view_{idx}"):
                    st.session_state["selected_job"] = job
                    st.session_state["current_step"] = "job_detail"
                    st.rerun()

def render_career_chat():
    """Career exploration chat interface"""
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "landing"
            st.rerun()
    
    st.markdown("### 💬 Career Exploration")
    st.markdown("Not sure what you're looking for? Let's explore your options together.")
    
    # Chat history
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    user_input = st.chat_input("Ask me anything about careers...")
    
    if user_input:
        # Add user message
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        
        # Get AI response
        response = career_chat(user_input, st.session_state["chat_history"])
        st.session_state["chat_history"].append({"role": "assistant", "content": response})
        
        st.rerun()

def render_job_detail():
    """Job detail and decision point"""
    job = st.session_state.get("selected_job")
    if not job:
        st.session_state["current_step"] = "landing"
        st.rerun()
        return
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "search"
            st.rerun()
    
    st.markdown(f"## {job.get('title')}")
    st.markdown(f"**{job.get('company')}** • {job.get('location')} • {job.get('type', 'Full-time')}")
    st.markdown(f"Match Score: **{job.get('match_score', 0)}%**")
    
    st.markdown("---")
    
    st.markdown("### Job Description")
    st.markdown(job.get('description', 'No description available.'))
    
    if job.get('requirements'):
        st.markdown("### Requirements")
        for req in job['requirements']:
            st.markdown(f"- {req}")
    
    st.markdown("---")
    st.markdown("### Ready to proceed?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Need to Prepare?")
        st.markdown("Get personalized steps to become a stronger candidate")
        if st.button("Get Action Plan", use_container_width=True):
            st.session_state["current_step"] = "prepare"
            st.rerun()
    
    with col2:
        st.markdown("#### 🚀 Ready to Apply?")
        st.markdown("Tailor your resume and generate a cover letter")
        if st.button("Tailor Application", use_container_width=True):
            st.session_state["current_step"] = "apply"
            st.rerun()

def render_prepare():
    """Preparation/action plan view"""
    st.markdown("### 🎯 Becoming a Stronger Candidate")
    st.info("This feature will show personalized action plans based on the job requirements and your resume.")
    
    if st.button("← Back to Job"):
        st.session_state["current_step"] = "job_detail"
        st.rerun()

def render_apply():
    """Application tailoring view"""
    st.markdown("### 🚀 Tailor Your Application")
    st.info("This feature will tailor your resume and generate a cover letter.")
    
    if st.button("← Back to Job"):
        st.session_state["current_step"] = "job_detail"
        st.rerun()

# =========================
# Main App Router
# =========================

def main():
    current_step = st.session_state.get("current_step", "landing")
    
    if current_step == "landing":
        render_landing()
    elif current_step == "search":
        render_search_results()
    elif current_step == "chat":
        render_career_chat()
    elif current_step == "job_detail":
        render_job_detail()
    elif current_step == "prepare":
        render_prepare()
    elif current_step == "apply":
        render_apply()

if __name__ == "__main__":
    main()

