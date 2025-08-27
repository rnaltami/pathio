import os
import json
import html
import requests
import streamlit as st
from textwrap import dedent
from urllib.parse import quote, unquote
from pathlib import Path
import base64
# =========================
# Backend URL (single source of truth)
# =========================
DEFAULT_BACKEND = "https://pathio-c9yz.onrender.com"
backend_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND).rstrip("/")

# Optional tiny debug — helps confirm what the app is using in prod
# st.caption(f"Using backend: {backend_url}")

# =====================================================
# CLEAN CHAT VIEW (open via ?view=chat&prompt=...)
# =====================================================
qp = st.query_params  # Streamlit modern API
if qp.get("view") == "chat":
    seed = unquote(qp.get("prompt", "")) if qp.get("prompt") else ""

    # Page setup for the chat view only
    title = f"How‑to: {seed}" if seed else "How‑to Guide"
    st.set_page_config(page_title=title, page_icon="pathio-logo.png", layout="centered")
    st.markdown(f"### {title}")

    st.session_state.setdefault("chat_messages", [])

    # Optional: tiny local fallback so you can demo even if /coach isn't built yet
    def fallback_steps(prompt: str) -> str:
        t = prompt.lower()
        if "obs" in t or "live" in t:
            return (
                "**Quick plan:**\n"
                "1) Install OBS; add mic + screen in a Scene.\n"
                "2) Settings → Output: 720p/30fps; record a 3‑min dry run.\n"
                "3) Watch back; note 3 fixes (audio, framing, hook).\n"
                "4) Apply fixes; record a second take; save with notes.\n"
            )
        return (
            "**Starter steps:**\n"
            "1) Break the task into 4–6 steps with outcomes.\n"
            "2) Timebox step 1 to 20 minutes and start.\n"
            "3) Save evidence (doc/clip) and iterate once.\n"
        )

    # Seed first turn if arriving with a prompt (append only; render later to avoid duplicates)
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
                reply = (data.get("reply") or "").strip()
                if not reply:
                    reply = fallback_steps(seed)
            except Exception:
                reply = fallback_steps(seed)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

    # --- Render full history ---
    for m in st.session_state["chat_messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # --- Follow‑ups ---
    user_msg = st.chat_input("Ask a follow‑up…")
    if user_msg:
        # 1) add user turn
        st.session_state["chat_messages"].append({"role": "user", "content": user_msg})

        # 2) call backend
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
                    reply = (data.get("reply") or "").strip()
                    if not reply:
                        reply = "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"
                except Exception:
                    reply = "Here’s a short, concrete plan:\n1) Define the goal\n2) Gather tools\n3) Execute\n4) Review\n"
            st.markdown(reply)

        # 3) persist assistant turn, then rerun to show full thread
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

    # Prevent the main UI from rendering in chat view
    st.stop()

# =====================================================
# MAIN APP (Tailor → Download → Insights → Actions)
# =====================================================
st.set_page_config(page_title="Pathio", page_icon="pathio-logo.png", layout="centered")
st.markdown("""
<style>
:root{
  --bg:#fff; --text:#111; --muted:#666; --accent:#3366ff;
  --border:#e6e6e6; --panel:#f7f7f7; --radius:10px;
  --fs-0:12px; --fs-1:13px; --fs-2:14px; --fs-3:15px;
}

/* Base + push content below Streamlit header */
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text)!important;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial!important;line-height:1.35;font-size:var(--fs-3);}
.block-container{padding-top:60px!important;padding-bottom:22px!important;}
/* Optional: hide Streamlit's top bar */
/* header{visibility:hidden;} */

/* Keep headings small everywhere (incl. markdown previews) */
h1,h2,h3{margin:0 0 8px;}
h1{font-size:20px;font-weight:650;}
h2{font-size:16px;font-weight:650;}
h3{font-size:14px;font-weight:650;}
[data-testid="stMarkdownContainer"] h1{font-size:20px;}
[data-testid="stMarkdownContainer"] h2{font-size:16px;}
[data-testid="stMarkdownContainer"] h3{font-size:14px;}

/* Inputs */
.stTextInput input,.stTextArea textarea{
  background:var(--panel)!important;color:var(--text)!important;border:1px solid var(--border)!important;
  border-radius:var(--radius)!important;padding:10px 12px;font-size:var(--fs-2);
}
.stTextArea textarea{min-height:160px!important;max-height:180px!important;line-height:1.5!important;resize:vertical;}

/* Primary action button */
.stButton button{
  background:var(--accent)!important;color:#fff!important;border:none!important;
  border-radius:999px!important;padding:10px 20px!important;font-size:var(--fs-2);font-weight:600;cursor:pointer;
  transition:background .2s ease;
}
.stButton button:hover{background:#254eda!important;}

/* Card wrapper */
.card{
  background:#fff;border:1px solid var(--border);border-radius:12px;padding:12px;
  display:flex;flex-direction:column;gap:8px;min-height:120px;overflow:hidden;
}
.card + .card{margin-top:10px;}

/* Insights layout */
.insights-wrap{margin-top:14px;}
.insights-grid{
  display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;align-items:start;
  grid-auto-rows:minmax(60px,auto);
}
@media (max-width:900px){.insights-grid{grid-template-columns:1fr;}}

/* Score bar */
.score-box{margin-bottom:8px;}
.score-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
.score-label{font-size:var(--fs-1);color:var(--muted);}
.score-badge{font-size:var(--fs-1);font-weight:600;}
.score-bar{width:100%;height:5px;background:#eee;border-radius:999px;}
.score-fill{height:5px;background:var(--accent);border-radius:999px;}

/* Pills/list */
.pills{display:flex;flex-wrap:wrap;gap:6px;}
.pill{background:#f1f1f1;border:1px solid var(--border);border-radius:999px;padding:3px 8px;font-size:12px;}
.pill.warn{background:#fff7df;border-color:#f2e3b5;}
.clean-list{margin:0;padding-left:1.05rem;}
.clean-list li{font-size:var(--fs-1);margin-bottom:4px;}

/* Bottom spacer */
.block-container::after{content:"";display:block;height:90px;}

/* Fix ATS card overlap + spacing */
.insights-grid{ grid-auto-rows:minmax(120px,auto); }
.card .stMarkdown p:last-child, .card [data-testid="stMarkdownContainer"] p:last-child{ margin-bottom:0; }
.be-better{ clear:both;margin-top:20px; }
.ats-card{ min-height:160px; }
</style>
""", unsafe_allow_html=True)

# ---------- Brand header ----------
LOGO = Path(__file__).with_name("pathio-logo.png")  # rename as needed
logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()

# (optional) runtime check to confirm the file is present in Render
# st.caption(f"Logo exists: {LOGO.exists()} → {LOGO}")

st.markdown(
    f"""
    <div style="text-align:center; margin:0 0 12px 0;">
      <img src="data:image/png;base64,{logo_b64}" alt=":pathio" style="height:28px; width:auto;" />
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- State ----------
st.session_state.setdefault("pasted_resume", "")
st.session_state.setdefault("pasted_job", "")
st.session_state.setdefault("tailored", None)
st.session_state.setdefault("insights", None)

# ---------- Inputs ----------
resume_text = st.text_area(
    "Résumé input",
    key="pasted_resume",
    height=100,
    placeholder="Paste your résumé / CV",
    label_visibility="collapsed",
)
job_text = st.text_area(
    "Job description input",
    key="pasted_job",
    height=100,
    placeholder="Paste the job you want",
    label_visibility="collapsed",
)

st.markdown("---")

# ---------- Tailor ----------
if st.button("✨ Make it fit"):
    resume_txt = (st.session_state.get("pasted_resume") or "").strip()
    job_txt = (st.session_state.get("pasted_job") or "").strip()
    if not resume_txt or not job_txt:
        st.warning(
            f"Paste your résumé and the job description first.\n"
            f"(résumé chars: {len(resume_txt)}, job chars: {len(job_txt)})"
        )
    else:
        try:
            with st.spinner("Tailoring…"):
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

# ---------- Output ----------
tailored = st.session_state.get("tailored")
insights = st.session_state.get("insights")

if tailored:
    # Tailored résumé
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Tailored résumé (preview)")
    st.markdown(tailored.get("tailored_resume_md", ""), unsafe_allow_html=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # Cover letter
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Cover letter (preview)")
    st.markdown(tailored.get("cover_letter_md", ""), unsafe_allow_html=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # Downloads
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Download (.docx)")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download résumé"):
            try:
                p = {
                    "tailored_resume_md": tailored.get("tailored_resume_md", ""),
                    "cover_letter_md": tailored.get("cover_letter_md", ""),
                    "which": "resume",
                }
                rr = requests.post(f"{backend_url}/export", json=p, timeout=60)
                rr.raise_for_status()
                st.download_button(
                    "Save résumé",
                    data=rr.content,
                    file_name="pathio_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except Exception as e:
                st.error(f"Export failed: {e}")
    with col2:
        if st.button("Download cover letter"):
            try:
                p = {
                    "tailored_resume_md": tailored.get("tailored_resume_md", ""),
                    "cover_letter_md": tailored.get("cover_letter_md", ""),
                    "which": "cover",
                }
                rr = requests.post(f"{backend_url}/export", json=p, timeout=60)
                rr.raise_for_status()
                st.download_button(
                    "Save cover letter",
                    data=rr.content,
                    file_name="pathio_cover_letter.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except Exception as e:
                st.error(f"Export failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Insights ----------
if insights:
    try:
        if isinstance(insights, str):
            insights = json.loads(insights)
    except Exception:
        insights = {}

    score = int((insights or {}).get("match_score") or 0)
    missing = list((insights or {}).get("missing_keywords") or [])
    flags = list((insights or {}).get("ats_flags") or [])

    score_pct = max(0, min(score, 100))
    score_width = f"{score_pct}%"

    if missing:
        missing_html = '<div class="pills">' + "".join(
            f'<span class="pill warn">⚠️ {html.escape(str(kw))}</span>' for kw in missing
        ) + "</div>"
    else:
        missing_html = '<div class="caption">✅ No critical keywords missing</div>'

    if flags and not (len(flags) == 1 and str(flags[0]).lower() == "none"):
        flags_html = "<ul class='clean-list'>" + "".join(
            f"<li>⚠️ {html.escape(str(f))}</li>" for f in flags
        ) + "</ul>"
    else:
        flags_html = (
            '<div class="caption">'
            '✅ Your tailored résumé passed automated parsing checks (ATS) '
            'and should upload cleanly to job portals.'
            '</div>'
        )

    insights_iframe_html = dedent(f"""
    <style>
      :root {{
        --text:#333; --muted:#888; --border:#e6e6e6; --panel:#f7f7f7; --accent:#3366ff; --radius:12px;
      }}
      body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; color:var(--text); }}
      .insights-wrap {{ margin:8px 0 4px; display:grid; gap:12px; }}
      @media (min-width:720px) {{
        .insights-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
      }}
      .card {{ background:#fff; border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; }}
      .card h4 {{ margin:0 0 8px; font-size:14px; color:var(--muted); font-weight:600; }}
      .score-box {{ background:#fff; border:1px solid var(--border); border-radius:var(--radius); padding:14px; display:grid; gap:10px; }}
      .score-top {{ display:flex; align-items:center; justify-content:space-between; }}
      .score-label {{ color:var(--muted); font-size:13px; }}
      .score-badge {{ font-weight:700; font-size:18px; padding:6px 10px; border-radius:999px; background:#f0f8ff; border:1px solid #d9e7ff; color:#1e3a8a; }}
      .score-bar {{ height:8px; width:100%; background:#f2f2f2; border:1px solid var(--border); border-radius:999px; overflow:hidden; }}
      .score-fill {{ height:100%; background: linear-gradient(90deg,#60a5fa,#22c55e); }}
      .pills {{ display:flex; flex-wrap:wrap; gap:8px; }}
      .pill {{ display:inline-block; padding:6px 10px; border-radius:999px; font-size:13px; border:1px solid var(--border); background:#fff; color:#333; }}
      .pill.warn {{ background:#fff7ed; border-color:#fde68a; color:#92400e; }}
      .clean-list {{ margin:0; padding-left:18px; }}
      .clean-list li {{ margin:4px 0; }}
      .caption {{ color:#777; font-size:12px; }}
    </style>

    <div class="insights-wrap">
      <div class="score-box">
        <div class="score-top">
          <div class="score-label">Match score</div>
          <div class="score-badge">{score_pct}%</div>
        </div>
        <div class="score-bar"><div class="score-fill" style="width:{score_width};"></div></div>
      </div>

      <div class="insights-grid">
        <div class="card">
          <h4>Missing keywords</h4>
          {missing_html}
        </div>
        <div class="card">
          <h4>ATS checks</h4>
          {flags_html}
        </div>
      </div>
    </div>
    """).strip()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Insights")
    st.components.v1.html(insights_iframe_html, height=480, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Be a better candidate (ONLY if backend provides) ----------
    do_now = list((insights or {}).get("do_now") or [])
    do_long = list((insights or {}).get("do_long") or [])

    if do_now or do_long:
        def link_for(item_text: str) -> str:
            # Pass the exact action text as the prompt.
            href = f"?view=chat&prompt={quote(item_text)}"
            return f"<a class='chip' href='{href}' target='_blank' rel='noopener noreferrer'>Show me how</a>"

        st.markdown('<div class="card be-better">', unsafe_allow_html=True)
        st.markdown("#### Be a better candidate")
        colA, colB = st.columns(2)

        with colA:
            if do_now:
                st.markdown("**Do these now**")
                for text in do_now:
                    st.markdown(
                        f"• {html.escape(str(text))} {link_for(str(text))}",
                        unsafe_allow_html=True,
                    )

        with colB:
            if do_long:
                st.markdown("**Do these long term**")
                for text in do_long:
                    st.markdown(
                        f"• {html.escape(str(text))} {link_for(str(text))}",
                        unsafe_allow_html=True,
                    )
        st.markdown('</div>', unsafe_allow_html=True)

# ---------- Optional micro‑footer (uncomment to show) ----------
# st.markdown(
#     "<div style='text-align:center; color:#888; font-size:12px; margin-top:16px;'>"
#     "No data is stored. Refresh clears your inputs."
#     "</div>", unsafe_allow_html=True
# )
