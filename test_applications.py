
from src.services.application_service import (
    shortlist_internship,
    update_status,
    get_applications,
)

demo_internship = {
    "id": "INT001",
    "company": "TechNova Demo",
    "role": "Python Developer Intern",
    "location": "Surat",
    "match_score": 95.0,
    "apply_url": "https://example.com/python-internship",
}

shortlist_internship(demo_internship)
print("1. Internship shortlisted.")

updated = update_status("INT001", "Applied")
print(f"2. Status updated: {updated}")

applications = get_applications()

print("\n--- APPLICATION TRACKER ---")
for application in applications:
    print(
        application["company"],
        "|",
        application["role"],
        "|",
        application["status"],
        "|",
        application["match_score"],
    )
