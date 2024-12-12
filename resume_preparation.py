import streamlit as st
import os
import json

"""# Create a directory for saving skills if it doesn't exist
SKILLS_DATA_DIR = "skills_data"
os.makedirs(SKILLS_DATA_DIR, exist_ok=True)"""

def show_skills_management():
    st.title("Skills Management")
    
    # Initialize updated_skills if not exists
    if "updated_skills" not in st.session_state:
        # Combine skills with any special skills that are initially added
        st.session_state.updated_skills = list(set(st.session_state.skills))  # Combine and remove duplicates
        
    # Track modifications
    if "skills_modified" not in st.session_state:
        st.session_state.skills_modified = False
    
    # Create two columns
    col1, col2 = st.columns(2)

    # Display current/updated skills in the first column
    with col1:
        st.subheader("Current Skills List")
        # Display original skills from session state
        if st.session_state.skills:  # Changed from updated_skills to skills
            for skill in sorted(st.session_state.skills):  # Display original skills
                st.write(f"- {skill}")
            
            # Show newly added skills separately
            
            new_skills = [skill for skill in st.session_state.updated_skills 
                         if skill not in st.session_state.skills]
            if new_skills:
                for skill in sorted(new_skills):
                    st.write(f"- {skill} *(added)*")
        else:
            st.write("No skills added yet.")

    # Display job description skills in the second column
    with col2:
        st.subheader("Skills from Job Description")
        job_description_skills = st.session_state.get("special_skills", [])
        
        if job_description_skills:
            for idx, skill in enumerate(job_description_skills):  # Use enumerate to get index
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    if skill in st.session_state.updated_skills:
                        st.write(f"- {skill} *(added)*")
                    else:
                        st.write(f"- {skill}")
                with col_b:
                    button_label = "Remove" if skill in st.session_state.updated_skills else "Add"
                    # Make the key unique by combining skill with its index
                    if st.button(button_label, key=f"{skill}_{idx}"):  
                        if button_label == "Add":
                            st.session_state.updated_skills.append(skill)  # Add skill to updated_skills
                        else:
                            st.session_state.updated_skills.remove(skill)  # Remove skill from updated_skills
                        st.rerun()

    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Back", key="back_to_applicant_skills_btn"):
            st.session_state.page = "Job Description"
    with col2:
        if st.button("Next", key="next_to_analyze_jd"):
            st.session_state.final_skills = st.session_state.updated_skills.copy()
            st.session_state.page = "Analyze JD"




