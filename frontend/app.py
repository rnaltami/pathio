# app.py (Streamlit defaults — no custom CSS/HTML)
import os
import json
import html
import hashlib
import requests
import streamlit as st
import re

from textwrap import dedent
from urllib.parse import quote, unquote

# =========================
# Backend URL (single source of truth)
# =========================
DEFAULT_BACKEND = "https://pathio-c9yz.onrender.com"
backend_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND).rstrip("/")

# Tiny debug so you can confirm which backend is in use
st.caption(f"Using backend: {backend_url}")

# =====================================================
# ALT VIEWS
# =====================================================
qp = st.query_params

# ----- Chat helper view (?view=chat&prompt=...) -----
if qp.get("view") == "chat":
    seed = unquote(qp.get("prompt", "")) if qp.get("prompt") else ""
    title = f"How-to: {seed}" if seed else "How-to Guide"
    st.set_page_config(page_title=title, page_icon="pathio-logo.png", layout="centered")

    st.title(title)
    st.divider()

    st.session_state.setdefault("chat_messages", [])

    def fallback_steps(prompt: str) -> str:
        t = prompt.lower()
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

# ----- Future jobs placeholder (?view=future) -----
if qp.get("view") == "future":
    st.set_page_config(page_title="Explore jobs", page_icon="pathio-logo.png", layout="centered")
    st.title("Explore future jobs")
    st.info("This page is coming soon. (You landed here via the link under the job box.)")
    st.stop()

# =====================================================
# MAIN APP (Streamlit default styling)
# =====================================================
st.set_page_config(page_title="Pathio", page_icon="pathio-logo.png", layout="centered")

# ---------- Header ----------
st.markdown(
    """
    <div style="text-align:center; margin-bottom:1.5rem;">
        <div style="font-size:42px; font-weight:700; margin-bottom:4px;">
            :PATHIO
        </div>
        <p class="tagline">
            Tailor your résumé for the job.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Global Styles ----------
st.markdown(
    """
    <style>
      /* ========= Typographic scale ========= */
      /* Big: logo handled inline (42px) */
      /* Medium: tagline, buttons, section titles */
      .tagline,
      .stButton button,
      .section-title {
        font-size:16px !important;
        font-weight:600 !important;  /* titles a touch bolder */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
          Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif !important;
      }

      /* Small: user-entered text & captions */
      textarea, .stTextInput input {
        font-size:13px !important;
        font-weight:400 !important;
      }

      /* Placeholder text = medium */
      textarea::placeholder,
      .stTextInput input::placeholder {
        font-size:16px !important;
        font-weight:400 !important;
        opacity:0.75;
      }

      /* Captions = even smaller */
      .stCaption, footer, .stMarkdown small {
        font-size:12px !important;
        opacity:0.8;
      }

      /* ========= Result boxes ========= */
      .result-box {
        padding:12px 14px;
        border-radius:10px;
        border:1px solid rgba(0,0,0,0.08);
        margin:8px 0 18px 0;
      }
      @media (prefers-color-scheme: light) {
        .result-box { background:#f7f9ff; } /* light indigo tint */
      }
      @media (prefers-color-scheme: dark) {
        .result-box { background:#111827; border-color:rgba(255,255,255,0.08); }
      }

      /* Make everything INSIDE the result box small & tight */
      .result-box * {
        font-size:13px !important;
        line-height:1.5 !important;
        margin-top:0.25rem;
        margin-bottom:0.25rem;
      }
      .result-box h1, .result-box h2, .result-box h3,
      .result-box h4, .result-box h5, .result-box h6 {
        font-size:13.5px !important;
        font-weight:600 !important;
        margin-top:0.35rem !important;
        margin-bottom:0.35rem !important;
      }

      /* Section titles (use instead of st.subheader for medium size) */
      .section-title { margin:14px 0 6px 0; }

      /* Normalize global markdown heading sizes (outside boxes) */
      .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-size:16px !important;
        font-weight:600 !important;
        margin:12px 0 6px 0 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- State ----------
st.session_state.setdefault("pasted_resume", "")
st.session_state.setdefault("pasted_job", "")
st.session_state.setdefault("tailored", None)
st.session_state.setdefault("insights", None)

# If we have results, hide the tagline via CSS
if st.session_state.get("tailored"):
    st.markdown("<style>.tagline{display:none !important;}</style>", unsafe_allow_html=True)

# ---------- Inputs ----------
job_text = st.text_area(
    "Job description input",
    key="pasted_job",
    height=120,
    placeholder="Paste job listing.",
    label_visibility="collapsed",
)
st.markdown(
    "<div style='text-align:right; font-size:13px; margin-top:-8px;'>"
    "<a href='?view=future' style='text-decoration:none;'>explore jobs →</a>"
    "</div>",
    unsafe_allow_html=True,
)

resume_text = st.text_area(
    "Résumé input",
    key="pasted_resume",
    height=160,
    placeholder="Paste résumé.",
    label_visibility="collapsed",
)

# ---------- Tailor (button + handler) ----------
if st.button("Update résumé + create cover letter", key="cta"):
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

# Only show the helper line until results exist
if not st.session_state.get("tailored"):
    st.caption("＋ insights and clear steps to improve your match for the role.")

# ---------- Helper: split out "What changed" ----------
def split_what_changed(md: str):
    """
    Split the tailored resume Markdown into (main_md, changes_md).
    If no 'What changed' section is present, returns (md, None).
    """
    if not md:
        return "", None
    m = re.search(r'(?im)^\s*\*\*what changed\*\*\s*', md)
    if not m:
        return md, None
    main_md = md[:m.start()].rstrip()
    changes_md = md[m.start():].lstrip()  # keep the **What changed** header
    return main_md, changes_md

# ---------- Helper: split out "**Summary**" to its own card ----------
def split_summary(md: str):
    """
    Find a '**Summary**' header and return (summary_md, rest_md).
    We treat the summary as the header plus its following bullet block.
    If no summary found, returns (None, md).
    """
    if not md:
        return None, md
    lines = md.splitlines()
    start = None
    # locate the line that is exactly '**Summary**' (case-insensitive)
    for i, line in enumerate(lines):
        if re.match(r'^\s*\*\*summary\*\*\s*$', line.strip(), re.IGNORECASE):
            start = i
            break
    if start is None:
        return None, md

    # collect the bullet block after the header
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

# ---------- Output ----------
tailored = st.session_state.get("tailored")
insights = st.session_state.get("insights")

if tailored:
    # --- Résumé (split “What changed”, then split out "Summary") ---
    resume_md_full = tailored.get("tailored_resume_md", "")
    main_md, changes_md = split_what_changed(resume_md_full)
    summary_md, body_md = split_summary(main_md)

    # Summary card (if present)
    if summary_md:
        st.markdown("<div class='section-title'>Summary</div>", unsafe_allow_html=True)
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(summary_md, unsafe_allow_html=False)
        st.markdown("</div>", unsafe_allow_html=True)

    # Résumé preview (without the Summary block)
    st.markdown("<div class='section-title'>Tailored résumé (preview)</div>", unsafe_allow_html=True)
    st.markdown("<div class='result-box'>", unsafe_allow_html=True)
    st.markdown(body_md if body_md else main_md, unsafe_allow_html=False)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Cover letter ---
    st.markdown("<div class='section-title'>Cover letter (preview)</div>", unsafe_allow_html=True)
    st.markdown("<div class='result-box'>", unsafe_allow_html=True)
    st.markdown(tailored.get("cover_letter_md", ""), unsafe_allow_html=False)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Downloads (one-click) ---
    st.markdown("<div class='section-title'>Downloads (.docx)</div>", unsafe_allow_html=True)

    # Use FULL resume for download (includes "What changed"). Change to `body_md` to exclude.
    resume_md = resume_md_full
    cover_md  = tailored.get("cover_letter_md", "")
    sig = hashlib.md5((resume_md + "||" + cover_md).encode("utf-8")).hexdigest()

    # Reset cached files if content changed
    if st.session_state.get("docx_sig") != sig:
        st.session_state["docx_sig"] = sig
        st.session_state["resume_docx"] = None
        st.session_state["cover_docx"] = None

    # Prepare files once if missing
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

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download résumé",
            data=st.session_state.get("resume_docx") or b"",
            file_name="pathio_resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=st.session_state.get("resume_docx") is None,
            key="dl_resume",
        )
    with col2:
        st.download_button(
            "Download cover letter",
            data=st.session_state.get("cover_docx") or b"",
            file_name="pathio_cover_letter.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=st.session_state.get("cover_docx") is None,
            key="dl_cover",
        )

    # --- What changed (optional separate box) ---
    if changes_md:
        st.markdown("<div class='section-title'>What changed</div>", unsafe_allow_html=True)
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(changes_md, unsafe_allow_html=False)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- Insights ----------
if insights:
    try:
        if isinstance(insights, str):
            insights = json.loads(insights)
    except Exception:
        insights = {}

    st.markdown("<div class='section-title'>Insights</div>", unsafe_allow_html=True)

    score = int((insights or {}).get("match_score") or 0)
    missing = list((insights or {}).get("missing_keywords") or [])
    flags = list((insights or {}).get("ats_flags") or [])

    # Match score
    st.write(f"**Match score:** {score}%")
    st.progress(max(0, min(score, 100)) / 100.0)

    # Missing keywords
    if missing:
        st.warning("Missing keywords")
        st.write("- " + "\n- ".join(html.escape(str(kw)) for kw in missing))
    else:
        st.success("No critical keywords missing")

    # ATS checks
    if flags and not (len(flags) == 1 and str(flags[0]).lower() == "none"):
        st.warning("ATS checks")
        st.write("- " + "\n- ".join(html.escape(str(f)) for f in flags))
    else:
        st.info("Passed automated parsing checks (ATS).")

    # Be a better candidate (if provided)
    do_now = list((insights or {}).get("do_now") or [])
    do_long = list((insights or {}).get("do_long") or [])
    if do_now or do_long:
        st.markdown("<div class='section-title'>Be a better candidate</div>", unsafe_allow_html=True)
        if do_now:
            st.write("**Do these now**")
            for text in do_now:
                href = f"?view=chat&prompt={quote(str(text))}"
                st.markdown(f"- {html.escape(str(text))} — [Show me how]({href})", unsafe_allow_html=False)
        if do_long:
            st.write("**Do these long term**")
            for text in do_long:
                href = f"?view=chat&prompt={quote(str(text))}"
                st.markdown(f"- {html.escape(str(text))} — [Show me how]({href})", unsafe_allow_html=False)
