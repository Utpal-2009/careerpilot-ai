
import json
from pathlib import Path

import pymupdf
from docx import Document

from src.services.groq_service import ask_groq


def extract_text(file_path: str) -> str:
    """Extract text from a PDF or DOCX resume."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        with pymupdf.open(path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)

    elif suffix == ".docx":
        document = Document(path)
        text = "\n".join(p.text for p in document.paragraphs)

    else:
        raise ValueError("Only PDF and DOCX files are supported.")

    if not text.strip():
        raise ValueError(
            "No text found. The resume may be scanned or image-based."
        )

    return text


def analyze_resume(file_path: str) -> dict:
    """Extract and analyze resume using Groq."""
    resume_text = extract_text(file_path)

    prompt = f"""
Analyze this resume and extract the candidate's information.

Return a JSON object with exactly these keys:
{{
  "name": "",
  "education": [],
  "skills": [],
  "projects": [],
  "experience": [],
  "preferred_roles": [],
  "preferred_locations": [],
  "internship_duration": ""
}}

Rules:
- Use only information present in the resume.
- Do not invent missing information.
- Use arrays for list fields.
- Return valid JSON only.

Resume text:
<resume>
{resume_text[:12000]}
</resume>
"""

    response = ask_groq(prompt, json_mode=True)

    try:
        result = json.loads(response)
    except json.JSONDecodeError as exc:
        print("DEBUG: Groq raw response:", repr(response))
        raise ValueError(
            "Groq returned invalid JSON. Check the debug response."
        ) from exc

    required_keys = {
        "name",
        "education",
        "skills",
        "projects",
        "experience",
        "preferred_roles",
        "preferred_locations",
        "internship_duration",
    }

    if not isinstance(result, dict) or not required_keys.issubset(result):
        raise ValueError("Groq response is missing required JSON fields.")

    return result
