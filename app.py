import asyncio
import os

import streamlit as st

from jd_agents import RoleInputs, generate_jd, generate_linkedin_post

SENIORITY_LEVELS = ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Manager", "Director"]
EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
WORK_MODES = ["Onsite", "Hybrid", "Remote"]

st.set_page_config(page_title="JD Generator", page_icon="📝", layout="wide")

st.title("📝 Job Description Generator")
st.caption(
    "Enter the role basics. An AutoGen writer agent drafts the JD, a reviewer agent checks it "
    "for consistency and inclusive language, and a third agent creates a LinkedIn hiring post."
)

if not os.environ.get("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY is not set. Paste your key into the .env file and restart the app.")
    st.stop()

with st.form("role_form"):
    st.subheader("Role basics")
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Job title *", placeholder="e.g. Junior Python Developer")
        department = st.text_input("Department *", placeholder="e.g. Engineering")
        seniority = st.selectbox("Seniority level", SENIORITY_LEVELS, index=1)
        employment_type = st.selectbox("Employment type", EMPLOYMENT_TYPES)
    with col2:
        work_mode = st.selectbox("Work mode", WORK_MODES, index=1)
        location = st.text_input("Location *", placeholder="e.g. Chennai, India")
        reports_to = st.text_input("Reports to *", placeholder="e.g. Engineering Manager")
    submitted = st.form_submit_button("Generate JD", type="primary")

if submitted:
    required = {
        "Job title": job_title,
        "Department": department,
        "Location": location,
        "Reports to": reports_to,
    }
    missing = [label for label, value in required.items() if not value.strip()]
    if missing:
        st.warning(f"Please fill in: {', '.join(missing)}")
    else:
        role = RoleInputs(
            job_title=job_title.strip(),
            department=department.strip(),
            seniority=seniority,
            employment_type=employment_type,
            work_mode=work_mode,
            location=location.strip(),
            reports_to=reports_to.strip(),
        )
        try:
            with st.status("Agents at work...", expanded=True) as status:
                st.write("✍️ Writer is drafting; reviewer is checking the draft...")
                jd = asyncio.run(generate_jd(role))
                st.write("📣 Creating the LinkedIn post...")
                post = asyncio.run(generate_linkedin_post(jd.jd_markdown))
                status.update(label="Done", state="complete", expanded=False)
            st.session_state["jd"] = jd
            st.session_state["post"] = post
        except Exception as exc:  # surface API/network errors in the UI
            st.error(f"Generation failed: {exc}")

if "jd" in st.session_state:
    jd = st.session_state["jd"]
    drafts = sum(1 for source, _ in jd.transcript if source == "jd_writer")

    if jd.approved:
        st.success(f"Approved by the reviewer after {drafts} draft(s).")
    else:
        st.warning(
            f"The reviewer did not approve the JD within {drafts} drafts. "
            "Check the latest version below before publishing."
        )

    jd_tab, post_tab = st.tabs(["Job Description", "LinkedIn Post"])
    with jd_tab:
        st.markdown(jd.jd_markdown)
    with post_tab:
        st.markdown(st.session_state["post"])
        st.caption("Copy-ready text (use the copy icon on the right):")
        st.code(st.session_state["post"], language=None, wrap_lines=True)
