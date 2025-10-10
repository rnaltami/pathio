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
    
    /* Global styles - PERPLEXITY STYLE */
    :root {
        --bg-primary: #FFFFFF;
        --text-primary: #202020;
        --text-secondary: #707070;
        --accent-primary: #20808D;
        --border-color: #E0E0E0;
    }
    
    /* Import a clean font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Override Streamlit's default background */
    .main, .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .block-container {
        max-width: 680px;
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        margin: 0 auto;
    }
    
    /* Consistent container for all content */
    .content-container {
        max-width: 680px;
        margin: 0 auto;
    }
    
    /* Custom text styles - UNIFORM SIZING */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 0.95rem !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: var(--text-primary) !important;
        font-size: 0.95rem !important;
        font-weight: 400 !important;
        margin: 0.3rem 0 !important;
    }
    
    /* Header/Brand - STANDS OUT */
    .pathio-header {
        text-align: center;
        margin-bottom: 2.5rem;
    }
    
    .pathio-logo {
        font-size: 1.8rem !important;
        font-weight: 400 !important;
        letter-spacing: -0.5px;
        color: #303030;
        margin-bottom: 0.3rem;
    }
    
    .pathio-tagline {
        display: none !important;
    }
    
    /* Inputs - WHITE BACKGROUND, NO SHADOW */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-size: 0.95rem !important;
        font-weight: 400 !important;
        padding: 0.75rem 1rem !important;
        transition: none !important;
        box-shadow: none !important;
    }
    
    /* Remove shadow AND border from input container */
    .stTextInput > div,
    .stTextInput > div > div {
        box-shadow: none !important;
        background: transparent !important;
        border: none !important;
    }
    
    /* Hide "Press Enter to apply" text */
    .stTextInput [data-testid="InputInstructions"],
    .stTextInput .instructions {
        display: none !important;
    }
    
    /* Force no border change on ANY state */
    .stTextInput > div > div > input:focus,
    .stTextInput > div > div > input:active,
    .stTextInput > div > div > input:focus-visible,
    .stTextInput > div > div > input:hover,
    .stTextArea > div > div > textarea:focus,
    .stTextArea > div > div > textarea:active,
    .stTextArea > div > div > textarea:focus-visible,
    .stTextArea > div > div > textarea:hover {
        border: 1px solid var(--border-color) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-secondary) !important;
        opacity: 0.7;
        font-weight: 400;
    }
    
    /* Buttons - CLEAN, NO BACKGROUND */
    .stButton > button {
        background-color: transparent !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 400 !important;
        font-size: 0.95rem !important;
        transition: opacity 0.2s ease !important;
        cursor: pointer !important;
        text-align: left !important;
    }
    
    .stButton > button:hover {
        opacity: 0.7;
    }
    
    /* Job title buttons - look like text, no border */
    .stButton > button[kind="secondary"] {
        border: none !important;
        padding: 0.5rem 0 !important;
        font-weight: 400 !important;
    }
    
    /* Job row - with top border separator */
    .job-row {
        border-top: 1px solid var(--border-color);
        padding: 1rem 0;
        cursor: pointer;
        transition: opacity 0.2s ease;
    }
    
    .job-row:hover {
        opacity: 0.7;
    }
    
    .job-row:first-child {
        border-top: none;
    }
    
    /* Primary button - MINIMAL (no hover fill) */
    .stButton > button[kind="primary"] {
        background-color: transparent !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        opacity: 0.7;
    }
    
    /* Cards/Containers - COMPACT */
    .job-card {
        background-color: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        transition: border-color 0.2s ease;
    }
    
    .job-card:hover {
        border-color: var(--accent-primary);
    }
    
    .job-card h3 {
        font-size: 0.95rem !important;
        margin: 0 0 0.25rem 0 !important;
    }
    
    .job-card p {
        font-size: 0.8rem !important;
        margin: 0.15rem 0 !important;
    }
    
    /* Chat messages - CONTAINED */
    .stChatMessage {
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        margin-bottom: 0.5rem !important;
        max-width: 680px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* Chat input - FORCE CONTAINED WIDTH */
    .stChatInputContainer {
        max-width: 680px !important;
        margin: 0 auto !important;
    }
    
    .stChatInputContainer > div {
        max-width: 680px !important;
        margin: 0 auto !important;
    }
    
    /* Target the actual chat input field */
    [data-testid="stChatInput"] {
        max-width: 680px !important;
        margin: 0 auto !important;
    }
    
    [data-testid="stChatInput"] > div {
        max-width: 680px !important;
    }
    
    /* Remove red border from chat input on focus */
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInput"] textarea:focus-visible {
        border-color: var(--border-color) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Hide form boxes */
    .stForm {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }
    
    /* Text links style - Perplexity */
    a {
        transition: opacity 0.2s ease;
    }
    
    a:hover {
        opacity: 0.7;
        text-decoration: none !important;
    }
    
    /* Dividers - SUBTLE */
    hr {
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 1rem 0;
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
    """Landing page - Results on same page like Perplexity"""
    render_header()
    
    # Main search field
    search_query = st.text_input(
        "search",
        placeholder="Search for a job... writer, data scientist, marketing manager",
        label_visibility="collapsed",
        key="main_search"
    )
    
    # Check if user typed and hit enter or if we have a search query
    current_search = st.session_state.get("main_search", "").strip()
    saved_query = st.session_state.get("search_query", "")
    
    # If user typed something new, update saved query
    if current_search and current_search != saved_query:
        st.session_state["search_query"] = current_search
        saved_query = current_search
    
    # Alternative actions - plain text links style
    st.markdown("""
        <div style='margin-top: 2rem; font-size: 0.9rem; line-height: 2;'>
            <a href="?action=career" style='color: var(--text-secondary); text-decoration: none; display: block;'>
                I need career guidance first →
            </a>
            <a href="?action=apply" style='color: var(--text-secondary); text-decoration: none; display: block;'>
                I already have a job listing I want to apply to. Help me get it →
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    # Handle URL actions
    qp = st.query_params
    if qp.get("action") == "career":
        st.session_state["current_step"] = "chat"
        st.query_params.clear()
        st.rerun()
    elif qp.get("action") == "apply":
        st.session_state["current_step"] = "paste_job"
        st.query_params.clear()
        st.rerun()
    
    # Show results on same page if we have a query
    if saved_query:
        st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
        
        with st.spinner("Searching..."):
            results = search_jobs(saved_query, st.session_state.get("user_resume"))
        
        if results:
            # Results header
            st.markdown(f"""
                <div style='margin-bottom: 1.5rem; font-size: 0.9rem; color: var(--text-secondary);'>
                    {len(results)} {saved_query} jobs found
                </div>
            """, unsafe_allow_html=True)
            
            # Refinement options
            st.markdown("""
                <div style='margin-bottom: 1.5rem; font-size: 0.85rem; color: var(--text-secondary);'>
                    Refine: <a href="?refine=remote" style='color: var(--text-secondary); text-decoration: underline;'>Remote only</a> • 
                    <a href="?refine=location" style='color: var(--text-secondary); text-decoration: underline;'>Change location</a>
                </div>
            """, unsafe_allow_html=True)
            
            # Job list with border separators
            for idx, job in enumerate(results):
                # Clickable job row
                job_key = f"job_btn_{idx}"
                if st.button(
                    f"{job.get('title', 'Job Title')}\n{job.get('company', 'Company')} • {job.get('location', 'Location')} • {job.get('type', 'Full-time')}",
                    key=job_key,
                    use_container_width=True,
                    type="secondary"
                ):
                    st.session_state["selected_job"] = job
                    st.session_state["current_step"] = "job_detail"
                    st.rerun()
                
                # Add visual separator after button
                if idx < len(results) - 1:
                    st.markdown("<div style='border-top: 1px solid var(--border-color); margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-top: 2rem; color: var(--text-secondary);'>No jobs found. Try a different search.</div>", unsafe_allow_html=True)

def render_paste_job():
    """Direct job paste interface for users who already have a listing"""
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "landing"
            st.rerun()
    
    st.markdown("### 📋 Paste Your Job Listing & Resume")
    st.markdown("We'll help you tailor your application")
    
    job_text = st.text_area(
        "job_listing",
        placeholder="Paste the job description here...",
        height=200,
        label_visibility="collapsed",
        key="paste_job_text"
    )
    
    st.markdown("**Your Resume:**")
    resume_text = st.text_area(
        "resume",
        placeholder="Paste your resume here...",
        height=250,
        label_visibility="collapsed",
        key="paste_resume_text"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Get Preparation Tips", use_container_width=True):
            if job_text and resume_text:
                st.session_state["pasted_job"] = job_text
                st.session_state["user_resume"] = resume_text
                st.session_state["current_step"] = "prepare_direct"
                st.rerun()
            else:
                st.warning("Please paste both job listing and resume")
    
    with col2:
        if st.button("🚀 Tailor Resume & Cover Letter", use_container_width=True, type="primary"):
            if job_text and resume_text:
                st.session_state["pasted_job"] = job_text
                st.session_state["user_resume"] = resume_text
                st.session_state["current_step"] = "apply_direct"
                st.rerun()
            else:
                st.warning("Please paste both job listing and resume")

def render_search_results():
    """Display job search results - PERPLEXITY STYLE"""
    query = st.session_state.get("search_query", "")
    
    # Clean back link (no border)
    st.markdown("""
        <a href="?back=true" style='color: var(--text-secondary); text-decoration: none; font-size: 0.9rem;'>
            ← Back to search
        </a>
    """, unsafe_allow_html=True)
    
    # Handle back action
    if st.query_params.get("back") == "true":
        st.session_state["current_step"] = "landing"
        st.query_params.clear()
        st.rerun()
    
    # Search results
    with st.spinner("Searching..."):
        results = search_jobs(query, st.session_state.get("user_resume"))
    
    if not results:
        st.markdown("<div style='margin-top: 2rem;'>No jobs found. Try a different search.</div>", unsafe_allow_html=True)
        return
    
    # Results header
    st.markdown(f"""
        <div style='margin: 1.5rem 0 1rem 0; font-size: 0.9rem; color: var(--text-secondary);'>
            {len(results)} {query} jobs found
        </div>
    """, unsafe_allow_html=True)
    
    # Refinement options (conversational)
    st.markdown("""
        <div style='margin-bottom: 2rem; font-size: 0.85rem; color: var(--text-secondary);'>
            Refine: <a href="?refine=remote" style='color: var(--text-secondary); text-decoration: underline;'>Remote only</a> • 
            <a href="?refine=location" style='color: var(--text-secondary); text-decoration: underline;'>Change location</a>
        </div>
    """, unsafe_allow_html=True)
    
    # Clean list of jobs (no borders, clickable titles)
    for idx, job in enumerate(results):
        # Make the whole job title clickable
        if st.button(
            job.get('title', 'Job Title'),
            key=f"job_{idx}",
            help=f"{job.get('company')} • {job.get('location')}",
            use_container_width=True
        ):
            st.session_state["selected_job"] = job
            st.session_state["current_step"] = "job_detail"
            st.rerun()
        
        # Company and location below (subtle)
        st.markdown(f"""
            <div style='margin: -0.5rem 0 1rem 0; font-size: 0.85rem; color: var(--text-secondary);'>
                {job.get('company', 'Company')} • {job.get('location', 'Location')} • {job.get('type', 'Full-time')}
            </div>
        """, unsafe_allow_html=True)

def render_career_chat():
    """Career exploration chat interface - CONTAINED"""
    # Wrap everything in a container
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back"):
        st.session_state["current_step"] = "landing"
        st.rerun()
    
    st.markdown("<div style='font-size: 1.1rem; font-weight: 500; margin: 1rem 0;'>Career Guidance</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem;'>Ask me anything about your career path</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat history - will be auto-contained by CSS
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input - will be auto-contained by CSS
    user_input = st.chat_input("Ask me anything...")
    
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
    """Preparation/action plan view - from job search flow"""
    job = st.session_state.get("selected_job")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "job_detail"
            st.rerun()
    
    st.markdown("### 🎯 Becoming a Stronger Candidate")
    
    # Call the better-candidate endpoint
    with st.spinner("Analyzing job requirements and creating your action plan..."):
        try:
            job_text = f"{job.get('title')} at {job.get('company')}\n\n{job.get('description')}"
            response = requests.post(
                f"{backend_url}/better-candidate",
                json={
                    "resume_text": st.session_state.get("user_resume", ""),
                    "job_text": job_text
                },
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                actions = data.get("actions", [])
                
                if actions:
                    st.markdown("**Here's your personalized action plan:**")
                    for action in actions:
                        with st.container():
                            st.markdown(f"### {action.get('title')}")
                            if action.get('why'):
                                st.markdown(f"*Why: {action.get('why')}*")
                            if action.get('steps'):
                                st.markdown("**Steps:**")
                                for step in action['steps']:
                                    st.markdown(f"- {step}")
                            st.markdown("---")
                else:
                    st.info("Upload your resume to get personalized recommendations.")
            else:
                st.error("Unable to generate action plan. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")

def render_prepare_direct():
    """Preparation from direct paste flow"""
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "paste_job"
            st.rerun()
    
    st.markdown("### 🎯 Your Personalized Action Plan")
    
    with st.spinner("Analyzing and creating your action plan..."):
        try:
            response = requests.post(
                f"{backend_url}/better-candidate",
                json={
                    "resume_text": st.session_state.get("user_resume", ""),
                    "job_text": st.session_state.get("pasted_job", "")
                },
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                actions = data.get("actions", [])
                
                if actions:
                    for action in actions:
                        with st.container():
                            st.markdown(f"### {action.get('title')}")
                            if action.get('why'):
                                st.markdown(f"*{action.get('why')}*")
                            if action.get('steps'):
                                st.markdown("**Steps:**")
                                for step in action['steps']:
                                    st.markdown(f"- {step}")
                            st.markdown("---")
                    
                    if st.button("Ready to Apply Now?", type="primary"):
                        st.session_state["current_step"] = "apply_direct"
                        st.rerun()
                else:
                    st.info("No specific actions needed - you look ready to apply!")
            else:
                st.error("Unable to generate action plan.")
        except Exception as e:
            st.error(f"Error: {e}")

def render_apply():
    """Application tailoring view - from job search flow"""
    job = st.session_state.get("selected_job")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "job_detail"
            st.rerun()
    
    st.markdown("### 🚀 Tailored Application")
    
    with st.spinner("Tailoring your resume and generating cover letter..."):
        try:
            job_text = f"{job.get('title')} at {job.get('company')}\n\n{job.get('description')}\n\nRequirements:\n" + "\n".join(f"- {req}" for req in job.get('requirements', []))
            
            response = requests.post(
                f"{backend_url}/quick-tailor",
                json={
                    "resume_text": st.session_state.get("user_resume", ""),
                    "job_text": job_text,
                    "user_tweaks": {}
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                
                tab1, tab2, tab3 = st.tabs(["Tailored Resume", "Cover Letter", "What Changed"])
                
                with tab1:
                    st.markdown(data.get("tailored_resume_md", ""))
                
                with tab2:
                    st.markdown(data.get("cover_letter_md", ""))
                
                with tab3:
                    st.markdown(data.get("what_changed_md", "No changes noted."))
                
                st.markdown("---")
                st.download_button(
                    "Download Resume",
                    data=data.get("tailored_resume_md", ""),
                    file_name="pathio_resume.md",
                    mime="text/markdown"
                )
            else:
                st.error("Unable to tailor application. Please try again.")
        except Exception as e:
            st.error(f"Error: {e}")

def render_apply_direct():
    """Application tailoring from direct paste flow"""
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "paste_job"
            st.rerun()
    
    st.markdown("### 🚀 Your Tailored Application")
    
    with st.spinner("Tailoring your resume and generating cover letter..."):
        try:
            response = requests.post(
                f"{backend_url}/quick-tailor",
                json={
                    "resume_text": st.session_state.get("user_resume", ""),
                    "job_text": st.session_state.get("pasted_job", ""),
                    "user_tweaks": {}
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                
                tab1, tab2, tab3 = st.tabs(["Tailored Resume", "Cover Letter", "What Changed"])
                
                with tab1:
                    st.markdown(data.get("tailored_resume_md", ""))
                
                with tab2:
                    st.markdown(data.get("cover_letter_md", ""))
                
                with tab3:
                    st.markdown(data.get("what_changed_md", "No changes noted."))
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "Download Resume",
                        data=data.get("tailored_resume_md", ""),
                        file_name="pathio_resume.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        "Download Cover Letter",
                        data=data.get("cover_letter_md", ""),
                        file_name="pathio_cover_letter.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
            else:
                st.error("Unable to tailor application.")
        except Exception as e:
            st.error(f"Error: {e}")

# =========================
# Main App Router
# =========================

def main():
    current_step = st.session_state.get("current_step", "landing")
    
    if current_step == "landing":
        render_landing()
    elif current_step == "paste_job":
        render_paste_job()
    elif current_step == "search":
        render_search_results()
    elif current_step == "chat":
        render_career_chat()
    elif current_step == "job_detail":
        render_job_detail()
    elif current_step == "prepare":
        render_prepare()
    elif current_step == "prepare_direct":
        render_prepare_direct()
    elif current_step == "apply":
        render_apply()
    elif current_step == "apply_direct":
        render_apply_direct()

if __name__ == "__main__":
    main()

