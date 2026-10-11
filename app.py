from src.services.access_control import verify_demo_access

import streamlit as st
import pandas as pd
import tempfile

from pathlib import Path

from src.services.resume_parser import (
    analyze_resume,
    extract_text,
)

from src.services.ats_checker import (
    check_ats_compatibility,
)

from src.services.resume_refiner import (
    refine_resume,
    create_docx,
)

from src.services.internship_search import (
    search_live_internships,
)

from src.services.application_service import (
    shortlist_internship,
    update_status,
    get_applications,
    remove_application,
)
# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CareerPilot AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)
# --------------------------------------------------
# DEMO ACCESS GATE
# --------------------------------------------------

if not verify_demo_access():
    st.stop()
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }
    .hero {
        padding: 1.5rem;
        border-radius: 16px;
        background: linear-gradient(120deg, #102A43, #176B87);
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        color: white;
        margin-bottom: 0.4rem;
    }
    .hero p {
        color: #E0F2FE;
        margin-bottom: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "profile" not in st.session_state:
    st.session_state.profile = None

if "matches" not in st.session_state:
    st.session_state.matches = None

if "resume_name" not in st.session_state:
    st.session_state.resume_name = None


if "resume_text" not in st.session_state:
    st.session_state.resume_text = None

if "ats_result" not in st.session_state:
    st.session_state.ats_result = None

if "refined_resume" not in st.session_state:
    st.session_state.refined_resume = None


# --------------------------------------------------
# HELPERS
# --------------------------------------------------


def analyze_uploaded_resume(uploaded_file):
    """Extract resume text and analyze the candidate profile."""

    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix not in {".pdf", ".docx"}:
        raise ValueError(
            "Please upload a PDF or DOCX resume."
        )

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_path = Path(temp_file.name)

    try:
        resume_text = extract_text(str(temp_path))
        profile = analyze_resume(str(temp_path))

        return profile, resume_text

    finally:
        temp_path.unlink(missing_ok=True)


def show_score(score):
    st.progress(max(0.0, min(float(score) / 100, 1.0)))
    st.caption(f"Match score: {score:.1f}%")


def render_internship(job, index):
    with st.container(border=True):
        st.subheader(job["role"])
        st.caption(
            f'{job["company"]} · {job.get("location", "Not specified")}'
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Match Score", f'{job["match_score"]:.1f}%')

        with col2:
            if job["eligible"]:
                st.success("Eligibility rules passed")
            else:
                st.warning("Eligibility rules not met")

        show_score(job["match_score"])

        matched = job.get("required_matched", [])
        missing = job.get("missing_required", [])

        st.write("**Required skills matched**")
        st.write(", ".join(matched) if matched else "No required skills matched.")

        st.write("**Missing required skills**")
        st.write(", ".join(missing) if missing else "No missing required skills.")

        with st.expander("Internship details"):
            st.write(job.get("description", "No description available."))
            st.write("**Work mode:**", job.get("work_mode", "Not specified"))
            st.write(
                "**Duration:**",
                f'{job.get("duration_months", "N/A")} months',
            )
            
            st.write("**Source:**", job.get("data_source") or job.get("source") or "Unknown")
            st.caption(
                "Live API listing. Verify the employer's page and vacancy status "
                "before applying."
            )
            
        col_a, col_b = st.columns(2)

        with col_a:
            if st.button(
                "⭐ Shortlist",
                key=f"shortlist_{job['id']}_{index}",
                width="stretch",
            ):
                shortlist_internship(job)
                st.success("Internship saved to your tracker.")
                st.rerun()

        with col_b:
            url = job.get("apply_url", "")
            if url:
                st.link_button(
                    "View listing",
                    url,
                    width="stretch",
                )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.title("🎯 CareerPilot AI")
    st.caption("AI Career & Internship Agent")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Resume Analyzer",
            "Internship Explorer",
            "Application Tracker",
        ],
    )

    st.divider()
    st.caption("Powered by Python, Groq and SQLite")
    st.caption("Demo listings are clearly labelled.")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "Dashboard":

    st.subheader("🎯 Find Your Internship")
    st.write("Choose your target role, preferred locations and resume.")

    with st.form("internship_search_form"):
        target_role = st.selectbox(
            "Target role",
            [
                "AI/ML Intern",
                "Python Developer Intern",
                "Web Developer Intern",
                "Java Developer Intern",
                "Cloud Engineer Intern",
                "Data Analyst Intern",
                "Any IT Internship",
            ],
        )

        locations = st.multiselect(
            "Preferred locations",
            [
                "Surat",
                "Ahmedabad",
                "Vadodara",
                "Gandhinagar",
                "Rajkot",
                "Anywhere in India",
            ],
            default=["Surat", "Ahmedabad"],
        )

        include_remote = st.checkbox(
            "Include remote internships",
            value=True,
        )

        resume_file = st.file_uploader(
            "Upload your resume",
            type=["pdf", "docx"],
            key="dashboard_resume_upload",
        )

        search_clicked = st.form_submit_button(
            "🔎 Find Matching Internships",
            type="primary",
            width="stretch",
        )

    if search_clicked:
        if not locations:
            st.warning("Please select at least one location.")
        elif resume_file is None:
            st.warning("Please upload your PDF or DOCX resume.")
        else:
            try:
                with st.spinner(
                    "Analyzing your resume and searching internships..."
                ):
                    profile, resume_text = analyze_uploaded_resume(resume_file)

                    # Use the user's current search preferences.
                    profile["preferred_roles"] = [target_role]
                    profile["preferred_locations"] = locations

                    matches = search_live_internships(
                        profile,
                        max_results=30,
                        search_role=target_role,
                        search_locations=locations,
                        include_remote=include_remote,
                    )

                st.session_state.profile = profile
                st.session_state.matches = matches
                st.session_state.resume_name = resume_file.name                
                st.session_state.resume_text = resume_text
                st.session_state.ats_result = None
                st.session_state.refined_resume = None

                st.session_state.search_preferences = {
                    "role": target_role,
                    "locations": locations,
                    "include_remote": include_remote,
                }

                st.success(
                    f"Search completed. {len(matches)} listings matched "
                    "your search and resume."
                )

            except Exception as error:
                st.error(f"Internship search failed: {error}")


    profile = st.session_state.profile

    if profile:
        st.divider()
        st.subheader("Candidate Profile")
        st.caption(f"Resume: {st.session_state.resume_name}")

        st.header(profile.get("name") or "Candidate")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Preferred roles**")
            st.write(
                ", ".join(profile.get("preferred_roles", []))
                or "Not specified"
            )

        with col2:
            st.write("**Preferred locations**")
            st.write(
                ", ".join(profile.get("preferred_locations", []))
                or "Not specified"
            )

        st.write("**Internship duration**")
        st.write(profile.get("internship_duration") or "Not specified")

        with st.expander("Technical skills", expanded=True):
            skills = profile.get("skills", [])
            st.write(f"**{len(skills)} skills extracted**")
            st.write(" · ".join(skills) if skills else "No skills found.")

        with st.expander("Education"):
            for item in profile.get("education", []):
                st.write(f"- {item}")

        with st.expander("Projects"):
            for item in profile.get("projects", []):
                st.write(f"- {item}")

        with st.expander("Experience"):
            for item in profile.get("experience", []):
                st.write(f"- {item}")

        with st.expander("Raw extracted profile"):
            st.json(profile)
        st.divider()
        st.subheader("🧾 AI Resume Improvement Center")

        st.caption(
            "Check basic ATS compatibility and improve your resume "
            "with AI while preserving your original information."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Check ATS Compatibility",
                key="check_ats_dashboard",
                width="stretch",
            ):
                try:
                    if not st.session_state.resume_text:
                        st.warning("Please analyze a resume first.")
                    else:
                        st.session_state.ats_result = (
                            check_ats_compatibility(
                                st.session_state.resume_text
                            )
                        )
                except Exception as error:
                    st.error(f"ATS check failed: {error}")

        with col2:
            if st.button(
                "✨ Refine Resume with AI",
                key="refine_resume_dashboard",
                type="primary",
                width="stretch",
            ):
                try:
                    if not st.session_state.resume_text:
                        st.warning("Please analyze a resume first.")
                    else:
                        with st.spinner(
                            "Groq is improving your resume..."
                        ):
                            st.session_state.refined_resume = (
                                refine_resume(
                                    st.session_state.resume_text,
                                    st.session_state.profile or {},
                                )
                            )
                except Exception as error:
                    st.error(
                        f"Resume refinement failed: {error}"
                    )

        # ATS results
        ats_result = st.session_state.ats_result

        if ats_result:
            st.markdown("### ATS Compatibility Results")

            metric1, metric2 = st.columns(2)

            with metric1:
                st.metric(
                    "Basic ATS Score",
                    f"{ats_result['score']}/100",
                )

            with metric2:
                st.metric(
                    "Word Count",
                    ats_result["word_count"],
                )

            st.progress(ats_result["score"] / 100)

            st.write("**Status:**", ats_result["status"])

            if ats_result["issues"]:
                st.write("**Items to review**")

                for item in ats_result["issues"]:
                    st.write(f"- {item}")

            if ats_result["suggestions"]:
                st.write("**Suggestions**")

                for item in ats_result["suggestions"]:
                    st.write(f"- {item}")

            st.caption(ats_result["disclaimer"])

        # Refined resume preview
        refined = st.session_state.refined_resume

        if refined:
            st.markdown("### Refined Resume Preview")

            st.markdown(
                refined["refined_resume_markdown"]
            )

            st.download_button(
                "⬇️ Download Refined Resume (.docx)",
                data=create_docx(
                    refined["refined_resume_markdown"]
                ),
                file_name="refined_resume.docx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                key="download_refined_resume_dashboard",
                width="stretch",
            )

            with st.expander("View AI changes and missing information"):
                st.write("**Changes made**")

                for item in refined.get("changes", []):
                    st.write(f"- {item}")

                missing = refined.get("missing_information", [])

                if missing:
                    st.write("**Information to verify or add manually**")

                    for item in missing:
                        st.write(f"- {item}")

            st.warning(
                "Review every detail before using this resume. "
                "Do not keep any inaccurate AI-generated statement."
            )

# --------------------------------------------------
# INTERNSHIP EXPLORER
# --------------------------------------------------
# --------------------------------------------------

elif page == "Internship Explorer":
    st.title("🔎 Internship Explorer")

    matches = st.session_state.matches

    if matches is None:
        st.info(
            "Analyze a resume first to generate personalized matches."
        )
    elif not matches:
        st.warning("No internship listings were found.")
    else:
        st.caption(
            
            f"{len(matches)} live API listings matched your search."

        )

        col1, col2 = st.columns(2)

        with col1:
            min_score = st.slider(
                "Minimum match score",
                min_value=0,
                max_value=100,
                value=0,
            )

        with col2:
            eligibility_filter = st.selectbox(
                "Eligibility",
                ["All", "Eligible only", "Not eligible"],
            )

        filtered = [
            job for job in matches
            if job["match_score"] >= min_score
            and (
                eligibility_filter == "All"
                or (
                    eligibility_filter == "Eligible only"
                    and job["eligible"]
                )
                or (
                    eligibility_filter == "Not eligible"
                    and not job["eligible"]
                )
            )
        ]

        st.write(f"**{len(filtered)} results**")

        if filtered:
            for index, job in enumerate(filtered):
                render_internship(job, index)
        else:
            st.warning("No listings match these filters.")


# --------------------------------------------------
# APPLICATION TRACKER
# --------------------------------------------------

elif page == "Application Tracker":
    st.title("📌 Application Tracker")
    st.write("Manage your shortlisted internships and application progress.")

    applications = get_applications()

    if not applications:
        st.info(
            "No applications saved yet. Shortlist an internship "
            "from Internship Explorer."
        )
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total tracked", len(applications))

        with col2:
            st.metric(
                "Applied",
                sum(item["status"] == "Applied" for item in applications),
            )

        with col3:
            st.metric(
                "Offers",
                sum(item["status"] == "Offer" for item in applications),
            )

        st.divider()

        df = pd.DataFrame(applications)

        display_columns = [
            "company",
            "role",
            "location",
            "match_score",
            "status",
        ]

        st.dataframe(
            df[display_columns],
            width="stretch",
            hide_index=True,
        )

        st.subheader("Update an application")

        selected_id = st.selectbox(
            "Choose an internship",
            options=[item["internship_id"] for item in applications],
            format_func=lambda internship_id: next(
                (
                    f"{item['company']} · {item['role']} "
                    f"({item['status']})"
                    for item in applications
                    if item["internship_id"] == internship_id
                ),
                internship_id,
            ),
        )

        selected_application = next(
            item for item in applications
            if item["internship_id"] == selected_id
        )

        statuses = [
            "Shortlisted",
            "Applied",
            "Interview",
            "Rejected",
            "Offer",
        ]

        current_status = selected_application["status"]

        if current_status not in statuses:
            current_status = "Shortlisted"

        new_status = st.selectbox(
            "Application status",
            statuses,
            index=statuses.index(current_status),
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Save status",
                type="primary",
                width="stretch",
            ):
                updated = update_status(selected_id, new_status)

                if updated:
                    st.success("Application status updated.")
                    st.rerun()
                else:
                    st.error("Application record was not updated.")

        with col2:
            if st.button(
                "Remove application",
                width="stretch",
            ):
                remove_application(selected_id)
                st.success("Application removed.")
                st.rerun()

        st.divider()

        st.subheader("Application details")

        for item in applications:
            with st.expander(
                f'{item["company"]} · {item["role"]}'
            ):
                st.write("**Status:**", item["status"])
                st.write("**Match score:**", f'{item["match_score"]}%')
                st.write("**Location:**", item.get("location", ""))
                st.write("**Created:**", item.get("created_at", ""))

                if item.get("apply_url"):
                    st.link_button(
                        "Open listing",
                        item["apply_url"],
                    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()
st.caption(
    "CareerPilot AI · Prototype · Verify internship details "
    "before applying. Demo listings are not live vacancies."
)
