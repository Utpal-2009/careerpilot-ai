"""Basic rule-based ATS resume compatibility checker."""

import re


SECTION_PATTERNS = {
    "Education": (
        r"(?im)^[ \t]*(education|academic background|qualifications)"
        r"[ \t]*:?[ \t]*$"
    ),
    "Skills": (
        r"(?im)^[ \t]*(technical skills|skills|core competencies)"
        r"[ \t]*:?[ \t]*$"
    ),
    "Projects": (
        r"(?im)^[ \t]*(projects|personal projects|academic projects)"
        r"[ \t]*:?[ \t]*$"
    ),
    "Experience": (
        r"(?im)^[ \t]*(experience|work experience|internship experience"
        r"|employment history)[ \t]*:?[ \t]*$"
    ),
}


def check_ats_compatibility(resume_text: str) -> dict:
    """Check basic resume formatting and contact details."""

    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError(
            "Resume text is empty. Upload a text-based PDF or DOCX."
        )

    text = resume_text.strip()
    words = re.findall(r"\b[\w+#.-]+\b", text)
    word_count = len(words)

    score = 0
    issues = []
    suggestions = []

    # Section headings: 4 × 15 = 60 points
    for section, pattern in SECTION_PATTERNS.items():
        if re.search(pattern, text):
            score += 15
        else:
            issues.append(f"Could not find a clear '{section}' heading.")
            suggestions.append(
                f"Add a clearly labelled '{section}' section if relevant."
            )

    # Email: 10 points
    email_pattern = r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"

    if re.search(email_pattern, text, re.IGNORECASE):
        score += 10
    else:
        issues.append("No email address detected.")
        suggestions.append(
            "Add a professional email address to the contact section."
        )

    # Phone number: 10 points
    phone_pattern = r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)"

    if re.search(phone_pattern, text):
        score += 10
    else:
        issues.append("No phone number detected.")
        suggestions.append(
            "Add a contact phone number if appropriate."
        )

    # Resume length: 10 points
    if 150 <= word_count <= 1000:
        score += 10
    else:
        issues.append(
            f"Resume contains {word_count} words. "
            "This check uses a simple guideline of 150–1000 words."
        )
        suggestions.append(
            "Review the resume length and keep relevant details concise."
        )

    # Bullet points: 10 points
    bullet_lines = re.findall(
        r"(?m)^[ \t]*[-*•][ \t]+\S.+$",
        text,
    )

    if len(bullet_lines) >= 2:
        score += 10
    else:
        issues.append("Fewer than two bullet-point lines were detected.")
        suggestions.append(
            "Use concise bullet points for projects and experience."
        )

    if score >= 80:
        status = "Good basic compatibility"
    elif score >= 55:
        status = "Needs improvement"
    else:
        status = "Several improvements recommended"

    if not suggestions:
        suggestions.append(
            "No issues were detected by these basic checks. "
            "Review the resume manually as well."
        )

    return {
        "score": min(score, 100),
        "status": status,
        "word_count": word_count,
        "issues": issues,
        "suggestions": suggestions,
        "disclaimer": (
            "This is a basic rule-based checklist, not a certified ATS "
            "score. Different employers and ATS products evaluate "
            "resumes differently."
        ),
    }