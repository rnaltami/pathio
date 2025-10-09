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
        max-width: 800px;
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    
    /* Custom text styles - INTER FONT */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: var(--text-primary) !important;
    }
    
    h1 { font-size: 1.5rem !important; margin: 0.5rem 0 !important; font-weight: 500 !important; }
    h2 { font-size: 1.25rem !important; margin: 0.5rem 0 !important; font-weight: 500 !important; }
    h3 { font-size: 1.1rem !important; margin: 0.4rem 0 !important; font-weight: 500 !important; }
    p { font-size: 0.9rem !important; margin: 0.3rem 0 !important; }
    
    /* Header/Brand - PERPLEXITY STYLE */
    .pathio-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .pathio-logo {
        font-size: 1.5rem;
        font-weight: 300;
        letter-spacing: -0.3px;
        color: #404040;
        margin-bottom: 0.25rem;
    }
    
    .pathio-tagline {
        font-size: 0.8rem;
        color: var(--text-secondary);
        font-weight: 400;
    }
    
    /* Inputs - PERPLEXITY STYLE (border only, no background) */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: transparent !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-size: 0.95rem !important;
        font-weight: 400 !important;
        padding: 0.75rem 1rem !important;
        transition: border-color 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--text-primary) !important;
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
        font-size: 0.85rem !important;
        transition: border-color 0.2s ease !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        border-color: var(--text-primary) !important;
    }
    
    /* Primary button style */
    .stButton > button[kind="primary"] {
        background-color: var(--text-primary) !important;
        color: white !important;
        border: 1px solid var(--text-primary) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9;
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
    
    /* Chat messages */
    .stChatMessage {
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        margin-bottom: 0.5rem !important;
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
    """Landing page - Perplexity style"""
    render_header()
    
    # Main search with button inside
    col1, col2 = st.columns([5, 1])
    with col1:
        search_query = st.text_input(
            "search",
            placeholder="Search for a job... writer, data scientist, marketing manager",
            label_visibility="collapsed",
            key="main_search"
        )
    with col2:
        st.markdown("<div style='padding-top: 0.1rem;'></div>", unsafe_allow_html=True)
        if st.button("Search", type="primary", use_container_width=True):
            if search_query:
                st.session_state["search_query"] = search_query
                st.session_state["current_step"] = "search"
                st.rerun()
    
    # Clean alternative text
    st.markdown("""
        <div style='margin: 2rem 0 1rem 0; text-align: center; font-size: 0.85rem; color: var(--text-secondary);'>
            Or
        </div>
    """, unsafe_allow_html=True)
    
    # Simple text buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("I need career guidance", use_container_width=True):
            st.session_state["current_step"] = "chat"
            st.rerun()
    with col2:
        if st.button("I already have a job to apply to", use_container_width=True):
            st.session_state["current_step"] = "paste_job"
            st.rerun()

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
    """Display job search results - COMPACT"""
    query = st.session_state.get("search_query", "")
    
    # Compact header
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← Back"):
            st.session_state["current_step"] = "landing"
            st.rerun()
    with col2:
        st.markdown(f"<div style='font-size: 0.95rem; padding-top: 0.3rem;'><strong>{query}</strong></div>", unsafe_allow_html=True)
    
    # Search results
    with st.spinner("Searching..."):
        results = search_jobs(query, st.session_state.get("user_resume"))
        
    if not results:
        st.info("No jobs found. Try a different search.")
        return
    
    st.markdown(f"<div style='font-size: 0.8rem; color: var(--text-secondary); margin: 0.5rem 0;'>{len(results)} jobs found</div>", unsafe_allow_html=True)
    
    for idx, job in enumerate(results):
        with st.container():
            st.markdown(f"""
                <div class="job-card">
                    <h3>{job.get('title', 'Job Title')}</h3>
                    <p style="color: var(--text-secondary);">
                        {job.get('company', 'Company')} • {job.get('location', 'Location')}
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("View", key=f"view_{idx}", use_container_width=False):
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

