import streamlit as st
import job_description
import resume_preparation
import analyze_bulletpoints
import professional_experience
import applicant_resume_upload
import preview_resume
import compare_results
import create_pdf
import word_similarity


# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "Applicant Resume Upload"  # Set the initial page

# Show the appropriate page based on the current state
if st.session_state.page == "Applicant Resume Upload":
    applicant_resume_upload.show_resume_upload_status()
elif st.session_state.page == "Applicant Personal Details":
    applicant_resume_upload.show_applicant_personal_details()
elif st.session_state.page == "Professional Summary and Work Experience":
    applicant_resume_upload.show_applicant_professional_summary_and_experience()
elif st.session_state.page == "Qualifications and Skills":
    applicant_resume_upload.show_applicant_skills_education_achievements()
elif st.session_state.page == "Job Description":
    job_description.show_job_description()
elif st.session_state.page == "Skills Management":
    resume_preparation.show_skills_management()
elif st.session_state.page == "Analyze JD":
    analyze_bulletpoints.show_analyze_bp()
elif st.session_state.page == "Professional Experience":
    professional_experience.Show_professional_experience()
elif st.session_state.page == "Preview Resume":
    preview_resume.show_preview_resume()
elif st.session_state.page == "similarity":
    compare_results.show_similarity()
elif st.session_state.page == "word similarity":
    word_similarity.show_similar_words()
elif st.session_state.page == "create resume":
    create_pdf.create_resume()
else:    
    st.error("Page not found. Please check the navigation.")

