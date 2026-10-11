
def normalize(value):
    return " ".join(str(value).lower().strip().split())


def skill_matches(candidate_skill, job_skill):
    candidate_skill = normalize(candidate_skill)
    job_skill = normalize(job_skill)

    aliases = {
        "rest api": "rest apis",
        "scikit learn": "scikit-learn",
        "ml": "machine learning",
    }

    candidate_skill = aliases.get(candidate_skill, candidate_skill)
    job_skill = aliases.get(job_skill, job_skill)

    return candidate_skill == job_skill


def matching_skills(candidate_skills, job_skills):
    matched = []

    for required in job_skills:
        if any(
            skill_matches(candidate, required)
            for candidate in candidate_skills
        ):
            matched.append(required)

    return matched


def calculate_match(profile, internship):
    skills = profile.get("skills", [])
    required = internship.get("required_skills", [])
    preferred = internship.get("preferred_skills", [])

    required_matches = matching_skills(skills, required)
    preferred_matches = matching_skills(skills, preferred)

    required_score = (
        len(required_matches) / len(required) * 60
        if required else 60
    )

    preferred_score = (
        len(preferred_matches) / len(preferred) * 20
        if preferred else 20
    )

    roles = profile.get("preferred_roles", [])
    job_role = internship.get("role", "")

    role_relevant = any(
        normalize(role) in normalize(job_role)
        or normalize(job_role) in normalize(role)
        for role in roles
    )

    role_score = 10 if role_relevant else 0

    locations = profile.get("preferred_locations", [])
    job_location = normalize(internship.get("location", ""))

    location_relevant = (
        job_location == "remote"
        or any(
            normalize(location) == job_location
            for location in locations
        )
    )

    location_score = 10 if location_relevant else 0

    total = round(
        required_score
        + preferred_score
        + role_score
        + location_score,
        2,
    )

    education_text = " ".join(
        str(item) for item in profile.get("education", [])
    ).lower()

    accepted_education = [
        normalize(item)
        for item in internship.get("education", [])
    ]

    education_eligible = any(
        item in education_text
        for item in accepted_education
    )

    candidate_duration = str(
        profile.get("internship_duration", "")
    ).lower()

    duration_eligible = (
        f"{internship.get('duration_months', 0)} months"
        in candidate_duration
        or candidate_duration
        == str(internship.get("duration_months", 0))
    )

    eligible = education_eligible and duration_eligible

    return {
        "match_score": total,
        "eligible": eligible,
        "education_eligible": education_eligible,
        "duration_eligible": duration_eligible,
        "required_matched": required_matches,
        "missing_required": [
            skill for skill in required
            if skill not in required_matches
        ],
        "preferred_matched": preferred_matches,
        "role_relevant": role_relevant,
        "location_relevant": location_relevant,
    }
