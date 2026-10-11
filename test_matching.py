
from pathlib import Path

from src.services.resume_parser import analyze_resume
from src.services.matching_service import find_matching_internships


resume_folder = Path("data/resumes")

files = [
    file for file in resume_folder.iterdir()
    if file.suffix.lower() in {".pdf", ".docx"}
]

if not files:
    raise FileNotFoundError("No resume found in data/resumes/")

profile = analyze_resume(str(files[0]))
results = find_matching_internships(profile)

print(f"\nCandidate: {profile.get('name', 'Unknown')}")
print("\n--- INTERNSHIP MATCH RESULTS ---")

for job in results:
    print(f"\n{job['role']} - {job['company']}")
    print(f"Match score: {job['match_score']}%")
    print(f"Eligible: {job['eligible']}")
    print(f"Missing skills: {job['missing_required']}")
    print(f"Apply URL: {job['apply_url']}")
