
import os
import re
import requests

from dotenv import load_dotenv

load_dotenv()

API_URL = "https://jsearch.p.rapidapi.com/search-v2"

SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript",
    "react", "node.js", "flask", "django", "fastapi",
    "sql", "mysql", "mongodb", "firebase",
    "pandas", "numpy", "scikit-learn",
    "machine learning", "deep learning",
    "rest api", "git", "docker", "aws",
    "html", "css", "streamlit", "pytest",
]


# --------------------------------------------------
# 1. DATA CLEANING HELPERS
# --------------------------------------------------

def _clean_text(value):
    """Convert missing or invalid text into a safe string."""

    if value is None or isinstance(value, (dict, list)):
        return ""

    text = str(value).strip()

    if text.casefold() in {
        "", "none", "null", "n/a", "na", "undefined", "nan"
    }:
        return ""

    return text


def _first_text(*values):
    """Return the first non-empty text value."""

    for value in values:
        text = _clean_text(value)

        if text:
            return text

    return ""


def _clean_list(value):
    """Clean a list and remove duplicate values."""

    if not isinstance(value, list):
        return []

    result = []
    seen = set()

    for item in value:
        text = _clean_text(item)
        key = text.casefold()

        if text and key not in seen:
            result.append(text)
            seen.add(key)

    return result


def _profile_values(profile, key):
    """Read profile values safely."""

    if not isinstance(profile, dict):
        return []

    value = profile.get(key, [])

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if item is not None and str(item).strip()
        ]

    return []


def _valid_url(value):
    """Accept only HTTP or HTTPS application URLs."""

    url = _clean_text(value)

    if url.startswith(("https://", "http://")):
        return url

    return ""


# --------------------------------------------------
# 2. SKILL EXTRACTION
# --------------------------------------------------

def _extract_skills(description):
    text = _clean_text(description).casefold()
    found = []

    for skill in SKILL_KEYWORDS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text):
            found.append(skill)

    return found


# --------------------------------------------------
# 3. STRUCTURED LOCATION
# --------------------------------------------------

def _normalize_location(item):
    city = _clean_text(item.get("job_city"))
    state = _clean_text(item.get("job_state"))
    country = _clean_text(item.get("job_country"))

    parts = list(dict.fromkeys(
        part for part in [city, state, country] if part
    ))

    remote = item.get("job_is_remote") is True

    return {
        "city": city,
        "state": state,
        "country": country,
        "display": ", ".join(parts) or "Location not specified",
        "is_remote": remote,
    }


def _get_work_mode(item):
    if item.get("job_is_remote") is True:
        return "Remote"

    # Do not guess hybrid/on-site when the API does not say.
    return _first_text(
        item.get("job_workplace_type"),
        "Not specified",
    ).replace("_", " ").title()


# --------------------------------------------------
# 4. STRUCTURED SALARY
# --------------------------------------------------

def _numeric_value(value):
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return value

    return None


def _normalize_salary(item):
    minimum = _numeric_value(item.get("job_min_salary"))
    maximum = _numeric_value(item.get("job_max_salary"))

    return {
        "min": minimum,
        "max": maximum,
        "currency": _clean_text(
            item.get("job_salary_currency")
        ),
        "period": _clean_text(
            item.get("job_salary_period")
        ),
    }


# --------------------------------------------------
# 5. APPLICATION LINKS
# --------------------------------------------------

def _normalize_apply_options(item):
    options = item.get("apply_options", [])

    if not isinstance(options, list):
        return []

    result = []
    seen_urls = set()

    for option in options:
        if not isinstance(option, dict):
            continue

        url = _valid_url(option.get("apply_link"))

        if not url or url.casefold() in seen_urls:
            continue

        seen_urls.add(url.casefold())

        result.append({
            "publisher": _clean_text(
                option.get("publisher")
            ),
            "url": url,
            "is_direct": (
                option.get("is_direct") is True
            ),
        })

    return result


# --------------------------------------------------
# 6. INTERNSHIP CLASSIFICATION
# --------------------------------------------------

def _is_internship(item):
    """
    Retain listings with an explicit internship signal.
    Mixed Full-time and Internship listings are accepted.
    """

    title = _clean_text(item.get("job_title")).casefold()

    primary_type = _clean_text(
        item.get("job_employment_type")
    ).upper()

    employment_types = item.get(
        "job_employment_types", []
    )

    if not isinstance(employment_types, list):
        employment_types = []

    types = {
        _clean_text(value).upper()
        for value in employment_types
        if _clean_text(value)
    }

    explicit_type = (
        any("INTERN" in value for value in types)
        or "INTERN" in primary_type
        or "INTERNSHIP" in primary_type
    )

    title_signal = (
        "intern" in title
        or "internship" in title
    )

    return explicit_type or title_signal


# --------------------------------------------------
# 7. RESUME MATCHING
# --------------------------------------------------

def _calculate_match(profile, job):
    candidate_skills = {
        skill.casefold()
        for skill in _profile_values(profile, "skills")
    }

    job_skills = set(
        _extract_skills(
            job["description"] + " " + job["role"]
        )
    )

    matched = sorted(candidate_skills & job_skills)
    missing = sorted(job_skills - candidate_skills)

    # Skill overlap: 70 points
    if job_skills:
        skill_score = 70 * len(matched) / len(job_skills)
    else:
        skill_score = 0

    # Preferred role: 15 points
    preferred_roles = _profile_values(
        profile, "preferred_roles"
    )
    title = job["role"].casefold()

    if not preferred_roles:
        role_score = 7.5
    elif any(
        role.casefold() in title
        for role in preferred_roles
    ):
        role_score = 15
    elif any(
        any(word in title for word in role.casefold().split())
        for role in preferred_roles
    ):
        role_score = 8
    else:
        role_score = 0

    # Preferred location: 15 points
    preferred_locations = _profile_values(
        profile, "preferred_locations"
    )
    location = job["location"].casefold()

    if not preferred_locations:
        location_score = 7.5
    elif any(
        place.casefold() in location
        or location in place.casefold()
        for place in preferred_locations
    ):
        location_score = 15
    else:
        location_score = 0

    score = round(
        skill_score + role_score + location_score, 1
    )

    # Preserve fields expected by the existing app.py.
    job["match_score"] = min(score, 100.0)
    job["required_matched"] = matched
    job["missing_required"] = missing

    # This is a preliminary skills estimate, not employer
    # eligibility verification.
    job["eligible"] = bool(job_skills) and not missing

    # Additional structured match details.
    job["match_details"] = {
        "skill_score": round(skill_score, 1),
        "role_score": role_score,
        "location_score": location_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "is_estimate": True,
    }

    return job


# --------------------------------------------------
# 8. NORMALIZE ONE JOB
# --------------------------------------------------

def _normalize_job(item, profile):
    title = _clean_text(item.get("job_title"))
    company = _clean_text(item.get("employer_name"))
    description = _clean_text(item.get("job_description"))

    if not title or not company:
        return None

    if not _is_internship(item):
        return None

    location = _normalize_location(item)
    apply_options = _normalize_apply_options(item)

    apply_url = _valid_url(item.get("job_apply_link"))

    if not apply_url and apply_options:
        apply_url = apply_options[0]["url"]

    if not apply_url:
        return None

    job_id = _clean_text(item.get("job_id"))
    employment_types = _clean_list(
        item.get("job_employment_types", [])
    )

    highlights = item.get("job_highlights", {})

    if not isinstance(highlights, dict):
        highlights = {}

    qualifications = _clean_list(
        highlights.get("Qualifications", [])
    )
    responsibilities = _clean_list(
        highlights.get("Responsibilities", [])
    )
    benefits = _clean_list(
        highlights.get("Benefits", [])
    )

    salary = _normalize_salary(item)

    job = {
        # Existing application/UI fields
        "id": job_id or (
            f"{company}|{title}|{location['display']}"
        ),
        "role": title,
        "company": company,
        "location": location["display"],
        "description": description,
        "work_mode": _get_work_mode(item),
        "duration_months": None,
        "apply_url": apply_url,
        "source": _clean_text(item.get("job_publisher")),
        "posted_at": _clean_text(
            item.get("job_posted_at")
        ),
        "employment_type": _first_text(
            item.get("job_employment_type"),
            ", ".join(employment_types),
            "Internship",
        ),

        # Company information
        "company_logo": _valid_url(
            item.get("employer_logo")
        ),
        "company_website": _valid_url(
            item.get("employer_website")
        ),

        # Location information
        "location_details": location,
        "is_remote": location["is_remote"],

        # Internship requirements and details
        "is_internship": True,
        "employment_types": employment_types,
        "qualifications": qualifications,
        "responsibilities": responsibilities,
        "benefits": benefits,
        "required_education": item.get(
            "job_required_education"
        ) if isinstance(
            item.get("job_required_education"), dict
        ) else {},
        "required_experience": item.get(
            "job_required_experience"
        ) if isinstance(
            item.get("job_required_experience"), dict
        ) else {},

        # Compensation
        "salary": salary,

        # Application information
        "apply_options": apply_options,
        "is_direct_apply": (
            item.get("job_apply_is_direct") is True
        ),
        "application_deadline": _clean_text(
            item.get(
                "job_offer_expiration_datetime_utc"
            )
        ),
        "source_job_url": _valid_url(
            item.get("job_google_link")
        ),

        # Data provenance and quality
        "data_source": "JSearch",
        "data_quality": {
            "has_description": bool(description),
            "has_salary": (
                salary["min"] is not None
                or salary["max"] is not None
            ),
            "has_duration": False,
            "has_deadline": bool(
                _clean_text(
                    item.get(
                        "job_offer_expiration_datetime_utc"
                    )
                )
            ),
        },
    }

    return _calculate_match(profile, job)


# --------------------------------------------------
# 9. FETCH AND DEDUPLICATE LIVE INTERNSHIPS
# --------------------------------------------------

def search_live_internships(
    profile,
    max_results=30,
    search_role=None,
    search_locations=None,
    include_remote=True,):
    """
    Fetch JSearch V5 listings, normalize the response,
    remove duplicate jobs and rank them for the resume.
    """

    api_key = os.getenv("JSEARCH_API_KEY")
    api_host = os.getenv(
        "JSEARCH_API_HOST",
        "jsearch.p.rapidapi.com",
    )

    if not api_key:
        raise ValueError(
            "JSEARCH_API_KEY is missing from your .env file."
        )

    roles = _profile_values(profile, "preferred_roles")
    locations = _profile_values(
        profile, "preferred_locations"
    )

    role = roles[0] if roles else "software developer intern"
    location = locations[0] if locations else "Gujarat, India"

    query = f"{role} internship in {location}"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host,
    }

    params = {
        "query": query,
        "num_pages": "1",
        "country": "India",
        "location": location,
        "date_posted": "all",
        "work_from_home": "false",
    }

    try:
        response = requests.get(
            API_URL,
            headers=headers,
            params=params,
            timeout=25,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"JSearch API returned HTTP "
                f"{response.status_code}. "
                f"Response: {response.text[:1000]}"
            )

        payload = response.json()

    except requests.Timeout as exc:
        raise RuntimeError(
            "JSearch API timed out. Please try again."
        ) from exc

    except requests.RequestException as exc:
        raise RuntimeError(
            f"JSearch network error: {exc}"
        ) from exc

    except ValueError as exc:
        raise RuntimeError(
            "JSearch returned invalid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(
            "Unexpected JSearch response format."
        )

    if payload.get("status") != "OK":
        raise RuntimeError(
            "JSearch request unsuccessful: "
            + _clean_text(payload.get("message"))
        )

    # JSearch V5: data is a dictionary containing jobs.
    data = payload.get("data", {})

    if isinstance(data, dict):
        raw_jobs = data.get("jobs", [])
    elif isinstance(data, list):
        raw_jobs = data
    else:
        raw_jobs = []

    if not isinstance(raw_jobs, list):
        raise RuntimeError(
            "Unexpected JSearch jobs response format."
        )

    normalized = []
    seen = set()

    for item in raw_jobs:
        if not isinstance(item, dict):
            continue

        job = _normalize_job(item, profile)

        if job is None:
            continue

        # Cross-source duplicate key.
        # Same company + title + location counts as one job.
        identity = (
            job["company"].casefold(),
            job["role"].casefold(),
            job["location"].casefold(),
        )

        if identity in seen:
            continue

        seen.add(identity)
        normalized.append(job)

    normalized.sort(
        key=lambda job: job["match_score"],
        reverse=True,
    )

    if not isinstance(max_results, int) or max_results < 1:
        max_results = 10

    return normalized[:max_results]
