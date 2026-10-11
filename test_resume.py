
from pathlib import Path
from src.services.resume_parser import analyze_resume

resume_folder = Path("data/resumes")

files = [
    p for p in resume_folder.iterdir()
    if p.suffix.lower() in {".pdf", ".docx"}
]

if not files:
    print("No resume found in data/resumes/")
else:
    resume_path = files[0]
    print(f"Testing resume: {resume_path.name}")

    try:
        profile = analyze_resume(str(resume_path))
        print("\n--- EXTRACTED PROFILE ---")
        print(profile)
    except Exception as error:
        print(f"\nError: {error}")
