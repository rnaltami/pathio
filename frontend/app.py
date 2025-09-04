# app.py — centered layout, native bordered cards, tasteful polish, tabs kept
import os
import json
import html
import hashlib
import requests
import streamlit as st
import re
from urllib.parse import quote, unquote

# =========================
# Backend URL (single source of truth)
# =========================
DEFAULT_BACKEND = "https://pathio-c9yz.onrender.com"
backend_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND).rstrip("/")

st.caption(f"Using backend: {backend_url}")

# =====================================================
# ALT VIEWS
# =====================================================
qp = st.query_params

# ----- Chat helper view (?view=chat&prompt=...) -----
if qp.get("view") == "chat":
    seed = unquote(qp.get("prompt", "")) if qp.get("prompt") else ""
    st.set_page_config(
        page_title=("How-to" if not seed else f"How-to: {seed}"),
        page_icon="pathio-logo.png",
        layout="centered",
    )

    st.markdown(
        """
        <style>
          .chat-title { font-size:20px; font-weight:700; margin:4px 0 2px 0; letter-spacing:.2px; }
          .chat-subtle { font-size:13px; opacity:.75; margin-bottom:6px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    title = f"How-to: {seed}" if seed else "How-to Guide"
    st.markdown(f"<div class='chat-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown("<div class='chat-subtle'>Practical, step-by-step instructions.</div>", unsafe_allow_html=True)
    st.divider()

    st.session_state.setdefault("chat_messages", [])

    def fallback_steps(prompt: str) -> str:
        t = (prompt or "").lower()
        if "obs" in t or "live" in t:
            return (
                "**Quick plan:**\n"
                "1) Install OBS; add mic + screen in a Scene.\n"
                "2) Settings → Output: 720p/30fps; record a 3-min dry run.\n"
                "3) Watch back; note 3 fixes (audio, framing, hook).\n"
                "4) Apply fixes; record a second take; save with notes.\n"
            )
        return (
            "**Starter steps:**\n"
            "1) Break the task into 4–6 steps with outcomes.\n"
            "2) Timebox step 1 to 20 minutes and start.\n"
            "3) Save evidence (doc/clip) and iterate once.\n"
        )

    if seed and not st.session_state["chat_messages"]:
        st.session_state["chat_messages"].append({"role": "user", "content": seed})
        with st.spinner("Thinking…"):
            try:
                r = requests.post(
                    f"{backend_url}/coach",
                    json={"messages": st.session_state["chat_messages"]},
                    timeout=60,
                )
                r.raise_for_status()
                data = r.json()
                reply = (data.get("reply") or "").strip() or fallback_steps(seed)
            except Exception:
                reply = fallback_steps(seed)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

    for m in st.session_state["chat_messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_msg = st.chat_input("Ask a follow-up…")
    if user_msg:
        st.session_state["chat_messages"].append({"role": "user", "content": user_msg})
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    r = requests.post(
                        f"{backend_url}/coach",
                        json={"messages": st.session_state["chat_messages"]},
                        timeout=120,
                    )
                    r.raise_for_status()
                    data = r.json()
                    reply = (data.get("reply") or "").strip() or (
                        "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"
                    )
                except Exception:
                    reply = "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"
            st.markdown(reply)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

    st.stop()

# Hidden future page
if qp.get("view") == "future":
    st.set_page_config(page_title="Explore jobs", page_icon="pathio-logo.png", layout="centered")
    st.title("Explore future jobs")
    st.info("This page is coming soon.")
    st.stop()

# =====================================================
# MAIN APP
# =====================================================
st.set_page_config(page_title="Pathio", page_icon="pathio-logo.png", layout="centered")

# ---------- Global polish ----------
st.markdown(
    """
    <style>
      /* Center the main column, keep it airy */
      .main .block-container { max-width: 860px; padding-top: 2.0rem; padding-bottom: 2.0rem; }

      /* System stack, consistent weights */
      .app * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
          Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif !important;
      }

      /* Headline group */
      .brand { font-size:28px; font-weight:800; letter-spacing:.2px; margin:0; }
      .tagline { font-size:20px; font-weight:700; margin:.35rem 0 .1rem 0; }
      .value { font-size:14px; font-weight:500; margin:.35rem 0 .6rem 0; opacity:.95; }
      .instruction { font-size:13px; opacity:.85; margin:0; }

      textarea, .stTextInput input { font-size:13px !important; }
      textarea::placeholder, .stTextInput input::placeholder { font-size:16px !important; opacity:.75; }

      /* Native bordered containers: add padding + subtle shadow + large radius */
      [data-testid="stContainer"][aria-expanded="true"] > div,  /* collapsers */
      div[data-testid="stVerticalBlock"] > div:has(> div [data-testid="stTabs"]) /* results card with tabs */ {
        border-radius: 14px;
      }

      /* Use Streamlit's border=True; we just refine padding & shadow */
      .st-emotion-cache-1r6slb0, .st-emotion-cache-13ln4jf {
        padding: 14px 16px !important; /* container inner padding */
      }

      /* Subtle elevation on any bordered container (works broadly across themes) */
      div[role="region"][aria-label][tabindex="-1"] {
        box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 6px 24px rgba(0,0,0,.04);
      }

      /* Tabs: make active tab clearer, keep minimal */
      div[role="tablist"] {
        border-bottom: 1px solid rgba(0,0,0,.08);
        margin-bottom: 10px;
      }
      button[role="tab"][aria-selected="true"] {
        border-bottom: 2px solid #2563eb !important;  /* single accent */
        font-weight: 700 !important;
      }
      .stButton button {
        font-size:16px !important;
        font-weight:700 !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        background: #2563eb22;  /* soft tint */
        border: 1px solid #2563eb55;
      }
      .stButton button:hover { filter: brightness(0.98); }
      .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { font-size:16px !important; font-weight:700 !important; }
    </style>
    <div class="app"></div>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    """
    <div style="text-align:center; margin-bottom:.6rem;">
      <div class="brand">PATHIO</div>
      <p class="tagline">Be a better candidate.</p>
      <p class="value">Update your résumé and create a cover letter, plus insights to improve your chances.</p>
      <p class="instruction">Start with the job you want.</p>
      <div style="margin-top:6px; font-size:12px; opacity:.75;">Launching soon</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- State ----------
st.session_state.setdefault("pasted_resume", "")
st.session_state.setdefault("pasted_job", "")
st.session_state.setdefault("tailored", None)
st.session_state.setdefault("insights", None)

# ---------- Inputs (native bordered card; no empty wrappers) ----------
with st.container(border=True):
    job_text = st.text_area(
        "Job description input",
        key="pasted_job",
        height=120,
        placeholder="Paste job description.",
        label_visibility="collapsed",
    )
    resume_text = st.text_area(
        "Résumé input",
        key="pasted_resume",
        height=160,
        placeholder="Paste résumé.",
        label_visibility="collapsed",
    )
    if st.button("Update résumé + cover letter", key="cta"):
        resume_txt = (st.session_state.get("pasted_resume") or "").strip()
        job_txt = (st.session_state.get("pasted_job") or "").strip()
        if not resume_txt or not job_txt:
            st.warning(
                f"Paste your résumé and the job description first.\n"
                f"(résumé chars: {len(resume_txt)}, job chars: {len(job_txt)})"
            )
        else:
            try:
                with st.spinner("Updating…"):
                    payload = {"resume_text": resume_txt, "job_text": job_txt, "user_tweaks": {}}
                    r = requests.post(f"{backend_url}/quick-tailor", json=payload, timeout=120)
                    if r.status_code != 200:
                        st.error(f"Backend error {r.status_code}")
                        try:
                            st.write(r.json())
                        except Exception:
                            st.write(r.text)
                    else:
                        data = r.json()
                        st.session_state["tailored"] = {
                            "tailored_resume_md": data.get("tailored_resume_md", ""),
                            "cover_letter_md": data.get("cover_letter_md", ""),
                        }
                        st.session_state["insights"] = data.get("insights", {})
                        st.success("Tailoring complete.")
            except Exception as e:
                st.exception(e)

# Helpers
def split_what_changed(md: str):
    if not md:
        return "", None
    m = re.search(r'(?im)^\s*\*\*what changed\*\*\s*', md)
    if not m:
        return md, None
    main_md = md[:m.start()].rstrip()
    changes_md = md[m.start():].lstrip()
    return main_md, changes_md

def split_summary(md: str):
    if not md:
        return None, md
    lines = md.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*\*\*summary\*\*\s*$', line.strip(), re.IGNORECASE):
            start = i
            break
    if start is None:
        return None, md
    end = start + 1
    saw_bullet = False
    while end < len(lines):
        s = lines[end].strip()
        if s == "":
            end += 1
            continue
        if s.startswith(("-", "•", "*")):
            saw_bullet = True
            end += 1
            continue
        if saw_bullet:
            break
        break
    summary_md = "\n".join(lines[start:end]).strip()
    if summary_md.lower().strip() == "**summary**":
        return None, md
    rest_md = ("\n".join(lines[:start] + lines[end:])).strip()
    return summary_md, rest_md

# ---------- Results (only render card if we have content) ----------
tailored = st.session_state.get("tailored")
insights = st.session_state.get("insights")

if not tailored:
    st.caption("＋ insights and clear steps to improve your match for the role.")

if tailored:
    resume_md_full = tailored.get("tailored_resume_md", "")
    main_md, changes_md = split_what_changed(resume_md_full)
    summary_md, body_md = split_summary(main_md)
    cover_md = tailored.get("cover_letter_md", "")

    with st.container(border=True):
        # Dynamic tabs
        tab_labels = ["Résumé", "Cover Letter", "Downloads"]
        if changes_md:
            tab_labels.append("What changed")
        tab_labels += ["Insights", "Be a better candidate"]
        tabs = st.tabs(tab_labels)

        # Résumé tab
        with tabs[0]:
            if summary_md:
                st.subheader("Summary")
                st.markdown(summary_md.replace("**Summary**", "").strip(), unsafe_allow_html=False)
                st.divider()
            st.subheader("Tailored résumé (preview)")
            st.markdown(body_md if body_md else main_md, unsafe_allow_html=False)

        # Cover Letter tab
        with tabs[1]:
            st.subheader("Cover letter (preview)")
            st.markdown(cover_md, unsafe_allow_html=False)

        # Downloads tab
        with tabs[2]:
            st.subheader("Downloads (.docx)")
            resume_md = resume_md_full  # backend cleans for export

            sig = hashlib.md5((resume_md + "||" + cover_md).encode("utf-8")).hexdigest()
            if st.session_state.get("docx_sig") != sig:
                st.session_state["docx_sig"] = sig
                st.session_state["resume_docx"] = None
                st.session_state["cover_docx"] = None

            if st.session_state.get("resume_docx") is None or st.session_state.get("cover_docx") is None:
                with st.spinner("Preparing downloads…"):
                    try:
                        for which in ("resume", "cover"):
                            payload = {
                                "tailored_resume_md": resume_md,
                                "cover_letter_md": cover_md,
                                "which": which,
                            }
                            rr = requests.post(f"{backend_url}/export", json=payload, timeout=60)
                            rr.raise_for_status()
                            if which == "resume":
                                st.session_state["resume_docx"] = rr.content
                            else:
                                st.session_state["cover_docx"] = rr.content
                    except Exception as e:
                        st.error(f"Export failed: {e}")

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "Download résumé",
                    data=st.session_state.get("resume_docx") or b"",
                    file_name="pathio_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    disabled=st.session_state.get("resume_docx") is None,
                    key="dl_resume",
                )
            with c2:
                st.download_button(
                    "Download cover letter",
                    data=st.session_state.get("cover_docx") or b"",
                    file_name="pathio_cover_letter.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    disabled=st.session_state.get("cover_docx") is None,
                    key="dl_cover",
                )

        # What changed tab (optional)
        idx = 3
        if changes_md:
            with tabs[idx]:
                st.subheader("What changed")
                st.markdown(changes_md, unsafe_allow_html=False)
            idx += 1

        # Insights tab
        with tabs[idx]:
            try:
                if isinstance(insights, str):
                    insights = json.loads(insights)
            except Exception:
                insights = {}

            score = int((insights or {}).get("match_score") or 0)
            missing = list((insights or {}).get("missing_keywords") or [])
            flags = list((insights or {}).get("ats_flags") or [])

            st.subheader("Match")
            st.write(f"**Match score:** {score}%")
            st.progress(max(0, min(score, 100)) / 100.0)

            st.subheader("Keywords & checks")
            if missing:
                st.warning("Missing keywords")
                st.write("- " + "\n- ".join(html.escape(str(kw)) for kw in missing))
            else:
                st.success("No critical keywords missing")
            if flags and not (len(flags) == 1 and str(flags[0]).lower() == "none"):
                st.warning("ATS checks")
                st.write("- " + "\n- ".join(html.escape(str(f)) for f in flags))
            else:
                st.info("Passed automated parsing checks (ATS).")

        # Be a better candidate tab
        with tabs[idx + 1]:
            try:
                if isinstance(insights, str):
                    insights = json.loads(insights)
            except Exception:
                insights = {}
            do_now = list((insights or {}).get("do_now") or [])
            do_long = list((insights or {}).get("do_long") or [])

            st.subheader("Be a better candidate")
            if not (do_now or do_long):
                st.info("No action suggestions available yet.")
            else:
                if do_now:
                    st.write("**Do these now**")
                    for text in do_now:
                        href = f"?view=chat&prompt={quote(str(text))}"
                        st.markdown(f"- {html.escape(str(text))} — [Show me how]({href})")
                if do_long:
                    st.write("**Do these long term**")
                    for text in do_long:
                        href = f"?view=chat&prompt={quote(str(text))}"
                        st.markdown(f"- {html.escape(str(text))} — [Show me how]({href})")
