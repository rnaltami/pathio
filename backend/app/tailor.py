# backend/app/tailor.py

from .models import ResumeJSON, JobPostingJSON
from .config import settings   # <-- NEW
from openai import OpenAI      # <-- NEW

client = OpenAI(api_key=settings.openai_api_key)  # <-- NEW

SYSTEM_PROMPT = """
You are Pathio.ai, an ATS-aware career copilot. Output plain text/Markdown only.
No tables, images, headers/footers, or text boxes. Use concise, quantified bullets.
Mirror key language from the job description.
"""

async def tailor_documents(resume: ResumeJSON, job: JobPostingJSON, tweaks: dict | None = None):
    name = resume.name or "Candidate Name"
    role = (job.title or "Target Role").title()

    # Merge tweaks into prompt if needed
    tweak_text = ""
    if tweaks:
        tweak_text = "\nAdditional user tweaks:\n" + str(tweaks)

    # Create the prompt for OpenAI
    user_prompt = f"""
Resume JSON:
{resume.model_dump_json(indent=2)}

Job Posting JSON:
{job.model_dump_json(indent=2)}

Generate a tailored résumé and cover letter for the role: {role}.
{name} is the candidate.

{tweak_text}
"""

    # ---- OpenAI API call ----
    response = client.responses.create(
        model="gpt-4.1-mini",   # pick your preferred model
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
    )

    # Extract output text
    output_text = response.output_text

    # For simplicity, split into résumé and cover letter by a delimiter
    if "COVER LETTER:" in output_text:
        resume_md, cover_md = output_text.split("COVER LETTER:", 1)
    else:
        resume_md, cover_md = output_text, ""

    return {
        "tailored_resume_md": resume_md.strip(),
        "cover_letter_md": cover_md.strip()
    }
