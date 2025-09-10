# app.py — classic st.tabs style, Summary above body, prefetch exports, tab memory, no disabled CTA

import os
import json
import html
import hashlib
import requests
import streamlit as st
import re
from urllib.parse import quote, unquote
from concurrent.futures import ThreadPoolExecutor

# =========================
# Backend URL + warmup
# =========================
DEFAULT_BACKEND = "https://pathio-c9yz.onrender.com"
backend_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND).rstrip("/")

# Warm backend (ignore errors)
try:
    requests.get(f"{backend_url}/healthz", timeout=3)
except Exception:
    pass

# =========================
# Alt View: How-to chat
# =========================
qp = st.query_params
if qp.get("view") == "chat":
    seed = unquote(qp.get("prompt", "")) if qp.get("prompt") else ""
    st.set_page_config(page_title=("How-to" if not seed else f"How-to: {seed}"),
                       page_icon="pathio-logo.png", layout="centered")
    st.markdown(
        "<style>.chat-title{font-size:20px;font-weight:700;margin:4px 0 2px 0}.chat-subtle{font-size:13px;opacity:.75;margin-bottom:6px}</style>",
        unsafe_allow_html=True,
    )
    title = f"How-to: {seed}" if seed else "How-to Guide"
    st.markdown(f"<div class='chat-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown("<div class='chat-subtle'>Practical, step-by-step instructions.</div>", unsafe_allow_html=True)
    st.divider()
    st.session_state.setdefault("chat_messages", [])

    def fallback_steps(prompt: str) -> str:
        return ("**Starter steps:**\n"
                "1) Break the task into 4–6 steps with outcomes.\n"
                "2) Timebox step 1 to 20 minutes and start.\n"
                "3) Save evidence (doc/clip) and iterate once.\n")

    if seed and not st.session_state["chat_messages"]:
        st.session_state["chat_messages"].append({"role":"user","content":seed})
        try:
            r = requests.post(f"{backend_url}/coach", json={"messages": st.session_state["chat_messages"]}, timeout=60)
            r.raise_for_status(); data = r.json()
            reply = (data.get("reply") or "").strip() or fallback_steps(seed)
        except Exception:
            reply = fallback_steps(seed)
        st.session_state["chat_messages"].append({"role":"assistant","content":reply})

    for m in st.session_state["chat_messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_msg = st.chat_input("Ask a follow-up…")
    if user_msg:
        st.session_state["chat_messages"].append({"role":"user","content":user_msg})
        with st.chat_message("assistant"):
            try:
                r = requests.post(f"{backend_url}/coach", json={"messages": st.session_state["chat_messages"]}, timeout=120)
                r.raise_for_status(); data = r.json()
                reply = (data.get("reply") or "").strip() or fallback_steps(user_msg)
            except Exception:
                reply = fallback_steps(user_msg)
            st.markdown(reply)
        st.session_state["chat_messages"].append({"role":"assistant","content":reply})
        st.rerun()
    st.stop()

# Hidden placeholder page
if qp.get("view") == "future":
    st.set_page_config(page_title="Explore jobs", page_icon="pathio-logo.png", layout="centered")
    st.title("Explore future jobs")
    st.info("This page is coming soon.")
    st.stop()

# =========================
# MAIN APP
# =========================
st.set_page_config(page_title="Pathio", page_icon="pathio-logo.png", layout="centered")


# --- Hide Streamlit chrome & running banners (stable testids) ---
st.markdown("""
<style>
  /* Top-right toolbar (rerun/stop/running icon) */
  [data-testid="stToolbar"] { display: none !important; }
  /* Deploy button */
  [data-testid="stDeployButton"] { display: none !important; }
  /* Connection/status widgets that flash during reruns */
  [data-testid="stStatusWidget"],
  [data-testid="stConnectionStatus"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ---------- Style (restore your previous look) ----------
st.markdown(
    """
    <style>
      :root{
        --blue-700:#1d3a9b; --blue-600:#1e40af; --blue-500:#2563eb; --blue-100:#eef4ff;
        --ink-900:#0f172a; --ink-700:#334155; --ink-600:#475569; --border:#e6edf7; --white:#ffffff;
      }
      .main .block-container{ max-width:860px; padding-top:2rem; padding-bottom:2rem; }
      .app *{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen,Ubuntu,Cantarell,"Open Sans","Helvetica Neue",sans-serif!important; color:var(--ink-900); }
      .brand{ font-size:32px; font-weight:700; letter-spacing:.2px; margin:0; }
      .tagline{ font-size:16px; font-weight:400; color:var(--ink-700); margin:.4rem 0 1rem 0; line-height:1.5; }
      .stMarkdown p,.stMarkdown li{ font-size:13px!important; }
      .stMarkdown h1,.stMarkdown h2,.stMarkdown h3{ font-size:16px!important; font-weight:700!important; margin:12px 0 8px 0!important; }
      textarea,.stTextInput input{ font-size:13px!important; background:var(--white)!important; border:1px solid var(--border)!important; border-radius:12px!important; }
      textarea::placeholder,.stTextInput input::placeholder{ color:var(--ink-600)!important; opacity:.9!important; font-size:15px!important; }

      /* Remove Streamlit card chrome */
      .st-emotion-cache-1r6slb0, .st-emotion-cache-13ln4jf, div[role="region"][aria-label][tabindex="-1"]{
        padding:0!important; background:transparent!important; border:0!important;
        border-radius:0!important; box-shadow:none!important; overflow:visible!important;
      }

      /* Tabs (keep Streamlit's, just color) */
      div[role="tablist"]{
        border-bottom: 1px solid var(--border);
        margin-bottom: 10px;
      }
      button[role="tab"]{
        color: var(--ink-600) !important;
      }
      button[role="tab"][aria-selected="true"]{
        color: var(--ink-900) !important;
        border-bottom: 2px solid var(--blue-500) !important;
        font-weight: 700 !important;
        box-shadow: none !important;
      }
      button[role="tab"]::after { display: none !important; } /* kill red underline */
      .stAlert {display:none} /* no 'Updated' overlays or warnings by default */
      
      /* Step badges */
      .step-row{ display:flex; align-items:center; gap:.5rem; margin:8px 2px; }
      .step-badge{
        display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:999px;
        background:var(--blue-100); color:var(--blue-600); font-weight:700; font-size:12px; border:0;
      }
      .step-title{ font-weight:700; font-size:14px; color:var(--ink-900); }
      .step-hint{ font-weight:500; font-size:13px; color:var(--ink-600); margin-left:.35rem; }
    </style>
    <div class="app"></div>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    """
    <div style="text-align:center;margin-bottom:.6rem;">
      <div class="brand">PATHIO</div>
      <div class="tagline">
        ✔ Tailor your résumé<br>
        ✔ Generate a cover letter<br>
        ✔ Get steps to be a stronger candidate
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- State ----------
st.session_state.setdefault("pasted_resume", "")
st.session_state.setdefault("pasted_job", "")
st.session_state.setdefault("tailored", None)
st.session_state.setdefault("insights", None)
st.session_state.setdefault("resume_docx", None)
st.session_state.setdefault("cover_docx", None)
st.session_state.setdefault("docx_sig", None)
st.session_state.setdefault("resume_export_error", None)
st.session_state.setdefault("cover_export_error", None)
st.session_state.setdefault("busy", False)
st.session_state.setdefault("active_tab", "Updated résumé")  # remember current tab

# ---------- Helpers ----------
def split_summary(md: str):
    """Return (summary_md_without_header, rest_md) or (None, full_md)."""
    if not md:
        return None, md
    lines = md.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*\*\*summary\*\*\s*$', line.strip(), re.IGNORECASE):
            start = i; break
    if start is None:
        return None, md
    end = start + 1; saw_bullet = False
    while end < len(lines):
        s = lines[end].strip()
        if s == "": end += 1; continue
        if s.startswith(("-", "•", "*")): saw_bullet = True; end += 1; continue
        if saw_bullet: break
        break
    blk = "\n".join(lines[start:end]).strip()
    if blk.lower().strip() == "**summary**": return None, md
    return blk.replace("**Summary**", "").strip(), ("\n".join(lines[:start] + lines[end:])).strip()

def prefetch_exports(resume_md: str, cover_md: str):
    """Fetch resume + cover DOCX concurrently and cache in session_state."""
    sig = hashlib.md5((resume_md + "||" + cover_md).encode("utf-8")).hexdigest()
    if st.session_state.get("docx_sig") == sig and st.session_state.get("resume_docx") and st.session_state.get("cover_docx"):
        return
    st.session_state["docx_sig"] = sig
    st.session_state["resume_docx"] = None
    st.session_state["cover_docx"] = None
    st.session_state["resume_export_error"] = None
    st.session_state["cover_export_error"] = None

    def fetch(which: str):
        payload = {"tailored_resume_md": resume_md, "cover_letter_md": cover_md, "which": which}
        r = requests.post(f"{backend_url}/export", json=payload, timeout=40)
        ct = (r.headers.get("Content-Type") or "").lower()
        if r.ok and "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in ct:
            return r.content, None
        try:
            return None, r.text
        except Exception:
            return None, f"Export failed with status {r.status_code}."

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_res = ex.submit(fetch, "resume")
        fut_cov = ex.submit(fetch, "cover")
        res_bytes, res_err = fut_res.result()
        cov_bytes, cov_err = fut_cov.result()

    if res_err: st.session_state["resume_export_error"] = res_err
    else:       st.session_state["resume_docx"] = res_bytes
    if cov_err: st.session_state["cover_export_error"] = cov_err
    else:       st.session_state["cover_docx"] = cov_bytes

# ---------- Inputs (no disabled controls) ----------
with st.form("pathio_form", clear_on_submit=False):
    st.markdown("<div class='step-row'><div class='step-badge'>1</div><div class='step-title'>Start with the job you want</div><div class='step-hint'>Paste job description.</div></div>", unsafe_allow_html=True)
    st.text_area("Job description input", key="pasted_job", height=140, label_visibility="collapsed")

    st.markdown("<div class='step-row'><div class='step-badge'>2</div><div class='step-title'>Paste your résumé</div></div>", unsafe_allow_html=True)
    st.text_area("Résumé input", key="pasted_resume", height=160, label_visibility="collapsed")

    submitted = st.form_submit_button("Go", use_container_width=True)

if submitted:
    resume_txt = (st.session_state.get("pasted_resume") or "").strip()
    job_txt = (st.session_state.get("pasted_job") or "").strip()
    if not resume_txt or not job_txt:
        st.error("Please paste both the résumé and the job description.")
    else:
        if st.session_state["busy"]:
            pass
        else:
            st.session_state["busy"] = True
            try:
                with st.spinner("Updating…"):
                    payload = {"resume_text": resume_txt, "job_text": job_txt, "user_tweaks": {}}
                    r = requests.post(f"{backend_url}/quick-tailor", json=payload, timeout=120)
                    if r.status_code == 503:
                        try:
                            msg = r.json().get("error") or "Service temporarily unavailable."
                        except Exception:
                            msg = "Service temporarily unavailable."
                        st.error(msg)
                    else:
                        r.raise_for_status()
                        data = r.json()
                        st.session_state["tailored"] = {
                            "tailored_resume_md": data.get("tailored_resume_md", ""),
                            "cover_letter_md": data.get("cover_letter_md", ""),
                            "what_changed_md": data.get("what_changed_md", ""),
                        }
                        st.session_state["insights"] = data.get("insights", {})
                        # Prefetch downloads
                        try:
                            prefetch_exports(
                                st.session_state["tailored"]["tailored_resume_md"],
                                st.session_state["tailored"]["cover_letter_md"],
                            )
                        except Exception as e:
                            st.session_state["resume_export_error"] = f"{e}"
                            st.session_state["cover_export_error"] = f"{e}"
                        # Land user on first results tab
                        st.session_state["active_tab"] = "Updated résumé"
            except requests.exceptions.HTTPError as e:
                st.error(f"Update failed ({e.response.status_code}). Please try again.")
            except Exception as e:
                st.error(f"Update failed. {e}")
            finally:
                st.session_state["busy"] = False


# ---------- Results ----------
tailored = st.session_state.get("tailored")
insights = st.session_state.get("insights")

if tailored:
     # LLM failure banner (visible even with .stAlert hidden)
    if not st.session_state.get("llm_ok", True):
        st.markdown(
            """
            <div style="border:1px solid #fecaca; background:#fef2f2; color:#7f1d1d;
                        padding:10px 12px; border-radius:10px; font-weight:600; margin-bottom:8px;">
              AI service unavailable right now — showing heuristic-only insights.
            </div>
            """,
            unsafe_allow_html=True,
        )
    resume_md_full = tailored.get("tailored_resume_md", "") or ""
    changes_md = (tailored.get("what_changed_md") or "").strip() or None
    summary_md, body_md = split_summary(resume_md_full)
    cover_md = tailored.get("cover_letter_md", "") or ""

    # Build tab list and reorder so the active tab renders first (prevents snap-back after reruns)
    base_tabs = ["Updated résumé", "Cover letter", "Downloads"]
    if changes_md:
        base_tabs.append("What changed")
    base_tabs += ["Insights", "Be a better candidate"]

    active = st.session_state.get("active_tab", "Updated résumé")
    ordered = [active] + [t for t in base_tabs if t != active]
    tab_objs = st.tabs(ordered)

    # Make a name -> tab object map
    tab_map = {name: tab_objs[i] for i, name in enumerate(ordered)}

    # Updated résumé
    with tab_map["Updated résumé"]:
        if summary_md:
            st.markdown(summary_md)   # summary above the body
            st.markdown("")           # small spacer
        st.markdown(body_md if body_md else resume_md_full, unsafe_allow_html=False)

    # Cover letter
    with tab_map["Cover letter"]:
        st.markdown(cover_md, unsafe_allow_html=False)

    # Downloads (prefetched; instant buttons). Stay on this tab by keeping active_tab unchanged.
    with tab_map["Downloads"]:
        resume_blob = st.session_state.get("resume_docx")
        cover_blob = st.session_state.get("cover_docx")
        res_err = st.session_state.get("resume_export_error")
        cov_err = st.session_state.get("cover_export_error")

        c1, c2 = st.columns(2)
        with c1:
            if st.download_button(
                "Download résumé",
                data=resume_blob or b"",
                file_name="pathio_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                disabled=(resume_blob is None),
                key="dl_resume",
            ):
                st.session_state["active_tab"] = "Downloads"
                st.rerun()  # <- add this line
        if res_err and resume_blob is None:
            st.caption(f"Export issue: {res_err}")

        with c2:
            if st.download_button(
                "Download cover letter",
                data=cover_blob or b"",
                file_name="pathio_cover_letter.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                disabled=(cover_blob is None),
                key="dl_cover",
            ):
                st.session_state["active_tab"] = "Downloads"
                st.rerun()  # <- add this line
        
        if cov_err and cover_blob is None:
            st.caption(f"Export issue: {cov_err}")

    # What changed
    if changes_md:
        with tab_map["What changed"]:
            st.markdown(changes_md, unsafe_allow_html=False)

    # Insights
    with tab_map["Insights"]:
        try:
            if isinstance(insights, str):
                insights = json.loads(insights)
        except Exception:
            insights = {}
        score = int((insights or {}).get("match_score") or 0)
        missing = list((insights or {}).get("missing_keywords") or [])
        flags = list((insights or {}).get("ats_flags") or [])
        st.markdown(f"**Match score:** {score}%")
        st.progress(max(0, min(score, 100)) / 100.0)
        if missing:
            st.markdown("**Missing keywords**")
            st.write("- " + "\n- ".join(html.escape(str(kw)) for kw in missing))
        else:
            st.markdown("**No critical keywords missing**")
        if flags and not (len(flags) == 1 and str(flags[0]).lower() == "none"):
            st.markdown("**ATS checks**")
            st.write("- " + "\n- ".join(html.escape(str(f)) for f in flags))
        else:
            st.markdown("**Passed automated parsing checks (ATS).**")

    # Be a better candidate
    with tab_map["Be a better candidate"]:
        try:
            if isinstance(insights, str):
                insights = json.loads(insights)
        except Exception:
            insights = {}
        do_now = list((insights or {}).get("do_now") or [])
        do_long = list((insights or {}).get("do_long") or [])
        if not (do_now or do_long):
            st.markdown("_No action suggestions available yet._")
        else:
            if do_now:
                st.markdown("**Do these now**")
                for text in do_now:
                    href = f"?view=chat&prompt={quote(str(text))}"
                    st.markdown(f"- {html.escape(str(text))} — [Show me how]({href})")
            if do_long:
                st.markdown("**Do these long term**")
                for text in do_long:
                    href = f"?view=chat&prompt={quote(str(text))}"
                    st.markdown(f"- {html.escape(str(text))} — [Show me how]({href})")
