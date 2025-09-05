# app.py — pill tabs, no validation captions, disabled CTA until filled, friendly 503 handling
import os
import json
import html
import hashlib
import requests
import streamlit as st
import re
from urllib.parse import quote, unquote

DEFAULT_BACKEND = "https://pathio-c9yz.onrender.com"
backend_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND).rstrip("/")

qp = st.query_params

# ---------------- Chat helper ----------------
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
            r.raise_for_status()
            data = r.json(); reply = (data.get("reply") or "").strip() or fallback_steps(seed)
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
                r.raise_for_status()
                data = r.json(); reply = (data.get("reply") or "").strip() or fallback_steps(user_msg)
            except Exception:
                reply = fallback_steps(user_msg)
            st.markdown(reply)
        st.session_state["chat_messages"].append({"role":"assistant","content":reply})
        st.rerun()
    st.stop()

# ---------------- Main ----------------
st.set_page_config(page_title="Pathio", page_icon="pathio-logo.png", layout="centered")

st.markdown("""
<style>
:root{
  --blue-700:#1d3a9b; --blue-600:#1e40af; --blue-500:#2563eb; --blue-100:#eef4ff;
  --ink-900:#0f172a; --ink-700:#334155; --ink-600:#475569; --border:#e6edf7; --white:#ffffff;
}
.main .block-container{max-width:860px;padding-top:2rem;padding-bottom:2rem}
.app *{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto, Oyxgen,Ubuntu,Cantarell,"Open Sans","Helvetica Neue",sans-serif!important;color:var(--ink-900)}
.brand{font-size:32px;font-weight:700;letter-spacing:.2px;margin:0}
.tagline{font-size:16px;font-weight:400;color:var(--ink-700);margin:.4rem 0 1rem 0;line-height:1.5}
.stMarkdown p,.stMarkdown li{font-size:13px!important}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-size:16px!important;font-weight:700!important;margin:12px 0 8px 0!important}

/* Inputs */
textarea,.stTextInput input{font-size:13px!important;background:var(--white)!important;border:1px solid var(--border)!important;border-radius:12px!important}
textarea::placeholder,.stTextInput input::placeholder{color:var(--ink-600)!important;opacity:.9!important;font-size:15px!important}

/* Remove streamlit card chrome */
.st-emotion-cache-1r6slb0,.st-emotion-cache-13ln4jf,div[role="region"][aria-label][tabindex="-1"]{
  padding:0!important;background:transparent!important;border:0!important;border-radius:0!important;box-shadow:none!important;overflow:visible!important
}

/* Pill tabs */
div[role="tablist"]{display:flex;gap:6px;padding:6px;border:0!important;background:var(--blue-100);border-radius:12px;margin-bottom:12px}
button[role="tab"]{color:var(--blue-600)!important;background:transparent!important;border-radius:10px!important;padding:6px 10px!important;box-shadow:none!important;border:0!important;outline:none!important}
button[role="tab"]::after{display:none!important}
button[role="tab"][aria-selected="true"]{background:var(--white)!important;color:var(--blue-700)!important;border:1px solid var(--border)!important;box-shadow:0 1px 2px rgba(0,0,0,.03)!important}

/* Button */
.stButton button{font-size:16px!important;font-weight:700!important;border-radius:12px!important;padding:10px 16px!important;background:var(--blue-600)!important;color:#fff!important;border:1px solid var(--blue-600)!important}
.stButton button:hover{filter:brightness(0.97)}

/* Step badges */
.step-row{display:flex;align-items:center;gap:.5rem;margin:8px 2px}
.step-badge{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:999px;background:var(--blue-100);color:var(--blue-600);font-weight:700;font-size:12px;border:0}
.step-title{font-weight:700;font-size:14px;color:var(--ink-900)}
.step-hint{font-weight:500;font-size:13px;color:var(--ink-600);margin-left:.35rem}

/* Tiny hint under button */
.hint{font-size:12px;color:var(--ink-600);margin-top:4px}
</style>
<div class="app"></div>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style="text-align:center;margin-bottom:.6rem;">
  <div class="brand">PATHIO</div>
  <div class="tagline">
    ✔ Tailor your résumé<br>
    ✔ Generate a cover letter<br>
    ✔ Get steps to be a stronger candidate
  </div>
</div>
""", unsafe_allow_html=True)

# State
st.session_state.setdefault("pasted_resume", "")
st.session_state.setdefault("pasted_job", "")
st.session_state.setdefault("tailored", None)
st.session_state.setdefault("insights", None)

# Inputs (no captions)
st.markdown("<div class='step-row'><div class='step-badge'>1</div><div class='step-title'>Start with the job you want</div><div class='step-hint'>Paste job description.</div></div>", unsafe_allow_html=True)
job_text = st.text_area("Job description input", key="pasted_job", height=140, label_visibility="collapsed")

st.markdown("<div class='step-row'><div class='step-badge'>2</div><div class='step-title'>Paste your résumé</div></div>", unsafe_allow_html=True)
resume_text = st.text_area("Résumé input", key="pasted_resume", height=160, label_visibility="collapsed")

# CTA: disabled until both have content
disabled = not ((st.session_state.get("pasted_job") or "").strip() and (st.session_state.get("pasted_resume") or "").strip())
cta = st.button("Go", key="cta", disabled=disabled)
if disabled:
    st.markdown("<div class='hint'>Add both fields to continue.</div>", unsafe_allow_html=True)

# Submit
if cta and not disabled:
    try:
        with st.spinner("Updating…"):
            payload = {
                "resume_text": (st.session_state.get("pasted_resume") or "").strip(),
                "job_text": (st.session_state.get("pasted_job") or "").strip(),
                "user_tweaks": {},
            }
            r = requests.post(f"{backend_url}/quick-tailor", json=payload, timeout=120)
            if r.status_code == 503:
                # Friendly message from strict backend
                try:
                    msg = r.json().get("error") or "Service temporarily unavailable."
                except Exception:
                    msg = "Service temporarily unavailable."
                st.toast(msg, icon="⚠️")
            else:
                r.raise_for_status()
                data = r.json()
                st.session_state["tailored"] = {
                    "tailored_resume_md": data.get("tailored_resume_md", ""),
                    "cover_letter_md": data.get("cover_letter_md", ""),
                }
                st.session_state["insights"] = data.get("insights", {})
                st.toast("Updated.", icon="✅")
    except requests.exceptions.HTTPError as e:
        st.toast(f"Update failed ({e.response.status_code}). Please try again.", icon="⚠️")
    except Exception as e:
        st.toast(f"Update failed. {e}", icon="⚠️")

# Helpers
def split_what_changed(md: str):
    if not md: return "", None
    m = re.search(r'(?im)^\s*\*\*what changed\*\*\s*', md)
    if not m: return md, None
    return md[:m.start()].rstrip(), md[m.start():].lstrip()

def split_summary(md: str):
    if not md: return None, md
    lines = md.splitlines(); start = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*\*\*summary\*\*\s*$', line.strip(), re.IGNORECASE):
            start = i; break
    if start is None: return None, md
    end = start + 1; saw_bullet = False
    while end < len(lines):
        s = lines[end].strip()
        if s == "": end += 1; continue
        if s.startswith(("-", "•", "*")): saw_bullet = True; end += 1; continue
        if saw_bullet: break
        break
    summary_md = "\n".join(lines[start:end]).strip()
    if summary_md.lower().strip() == "**summary**": return None, md
    rest_md = ("\n".join(lines[:start] + lines[end:])).strip()
    return summary_md, rest_md

# Results
tailored = st.session_state.get("tailored")
insights = st.session_state.get("insights")

if tailored:
    resume_md_full = tailored.get("tailored_resume_md", "")
    main_md, changes_md = split_what_changed(resume_md_full)
    summary_md, body_md = split_summary(main_md)
    cover_md = tailored.get("cover_letter_md", "")

    tab_labels = ["Updated résumé", "Cover letter", "Downloads"]
    if changes_md: tab_labels.append("What changed")
    tab_labels += ["Insights", "Be a better candidate"]
    tabs = st.tabs(tab_labels)

    # Updated résumé
    with tabs[0]:
        if summary_md:
            st.markdown(summary_md.replace("**Summary**", "").strip(), unsafe_allow_html=False)
            st.divider()
        st.markdown(body_md if body_md else main_md, unsafe_allow_html=False)

    # Cover letter
    with tabs[1]:
        st.markdown(cover_md, unsafe_allow_html=False)

    # Downloads
    with tabs[2]:
        resume_md = resume_md_full  # backend export will clean Summary/What changed
        sig = hashlib.md5((resume_md + "||" + cover_md).encode("utf-8")).hexdigest()
        if st.session_state.get("docx_sig") != sig:
            st.session_state["docx_sig"] = sig
            st.session_state["resume_docx"] = None
            st.session_state["cover_docx"] = None

        def _fetch_doc(which: str, resume_md: str, cover_md: str):
            payload = {"tailored_resume_md": resume_md, "cover_letter_md": cover_md, "which": which}
            rr = requests.post(f"{backend_url}/export", json=payload, timeout=60)
            ctype = (rr.headers.get("Content-Type") or rr.headers.get("content-type") or "").lower()
            x_err = rr.headers.get("X-Exporter-Error")
            if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in ctype and not x_err:
                return rr.content, None
            try:
                return None, rr.text
            except Exception:
                return None, f"Export failed with status {rr.status_code}."

        if st.session_state.get("resume_docx") is None or st.session_state.get("cover_docx") is None:
            try:
                res_bytes, res_err = _fetch_doc("resume", resume_md, cover_md)
                cov_bytes, cov_err = _fetch_doc("cover", resume_md, cover_md)
                if res_err: st.toast(f"Resume export error: {res_err}", icon="⚠️")
                else: st.session_state["resume_docx"] = res_bytes
                if cov_err: st.toast(f"Cover export error: {cov_err}", icon="⚠️")
                else: st.session_state["cover_docx"] = cov_bytes
            except Exception as e:
                st.toast(f"Export failed: {e}", icon="⚠️")

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download résumé",
                data=st.session_state.get("resume_docx") or b"",
                file_name="pathio_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                disabled=st.session_state.get("resume_docx") is None, key="dl_resume")
        with c2:
            st.download_button("Download cover letter",
                data=st.session_state.get("cover_docx") or b"",
                file_name="pathio_cover_letter.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                disabled=st.session_state.get("cover_docx") is None, key="dl_cover")

    # What changed (optional)
    idx = 3
    if changes_md:
        with tabs[idx]:
            st.markdown(changes_md, unsafe_allow_html=False)
        idx += 1

    # Insights
    with tabs[idx]:
        try:
            if isinstance(insights, str): insights = json.loads(insights)
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
    with tabs[idx + 1]:
        try:
            if isinstance(insights, str): insights = json.loads(insights)
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
