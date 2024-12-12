import streamlit as st
from dotenv import load_dotenv
import json
import os

# Load environment variables
load_dotenv()

def show_preview_resume():
    st.title("Preview Resume")

    if "name" in st.session_state:
        # Retrieve data from session state
        applicant_data = {
            "name": st.session_state.name,
            "email": st.session_state.email,
            "mobile": st.session_state.mobile,
            "generated_prof_summary": st.session_state.generated_prof_summary,
            "education": st.session_state.education,
            "experience": st.session_state.updated_experience,
            "skills": st.session_state.updated_skills,
            "achievements": st.session_state.special_achievements,
        }
        # Define the directory for saving applicant JSON files
        UPDATED_APPLICANT_DIR = "updated_applicant"

        # Ensure the directory exists
        os.makedirs(UPDATED_APPLICANT_DIR, exist_ok=True)
        # Save applicant details to a text file
        file_name = f"{UPDATED_APPLICANT_DIR}/{applicant_data['name'].replace(' ', '_')}_resume.json"
        with open(file_name, "w", encoding="utf-8") as json_file:
            json.dump(applicant_data, json_file, indent=4, ensure_ascii=False)

        # Store the filename in the session state
        st.session_state.resume_file_path = file_name

        # Display applicant details
        st.header("Applicant Details")
        st.subheader("Name")
        st.write(applicant_data["name"])

        st.subheader("Telephone")
        st.write(applicant_data["mobile"])

        st.subheader("Email")
        st.write(applicant_data["email"])

        st.header("Professional Summary")
        st.write(applicant_data["generated_prof_summary"])

        st.header("Experience")
        if applicant_data["experience"]:
            for idx, exp in enumerate(applicant_data["experience"], start=1):
                st.subheader(f"Job {idx}")
                st.write(f"**Company:** {exp.get('company', 'Not found')}")
                st.write(f"**Position:** {exp.get('position', 'Not found')}")
                st.write(f"**Duration:** {exp.get('duration', 'Not found')}")
                st.write("**Responsibilities:**")
                for desc in exp.get("job_descriptions", ["Not found"]):
                    st.write(f"- {desc}")
        else:
            st.write("No experience data available.")

        st.header("Achievements")
        if applicant_data["achievements"] and applicant_data["achievements"][0] != "Not found":
            for achievement in applicant_data["achievements"]:
                st.write(f"- {achievement}")
        else:
            st.write("No achievements found.")

        st.header("Education")
        if applicant_data["education"] and applicant_data["education"][0] != "Not found":
            for edu in applicant_data["education"]:
                st.write(f"- {edu}")
        else:
            st.write("No education details found.")
        
        if st.button("Show similarity"):
            st.session_state.page = "similarity"

def initialize_session_optimized_variables():
    """
    Initialize session variables if they don't exist.
    """
    if "optimized_data_text" not in st.session_state:
        st.session_state.optimized_data_text = ""  # Initialize as an empty string
    if "generated_prof_summary" not in st.session_state:
        st.session_state.generated_prof_summary = ""
    if "updated_experience" not in st.session_state:
        st.session_state.updated_experience = []
    if "updated_skills" not in st.session_state:
        st.session_state.updated_skills = []
    if "special_achievements" not in st.session_state:
        st.session_state.special_achievements = []

initialize_session_optimized_variables()

def save_optimized_resume_as_text():
    """
    Collects optimized resume data, saves it as text in the 'updated_applicant' directory,
    and stores the text in session state.
    """
    # Collect data from session state
    optimized_data = {
        "Generated Professional Summary": st.session_state.generated_prof_summary,
        "Experience": st.session_state.updated_experience,
        "Skills": st.session_state.updated_skills,
        "Special Achievements": st.session_state.special_achievements,
    }

    # Create a plain text representation of the optimized data
    optimized_data_lines = []
    for key, value in optimized_data.items():
        if isinstance(value, list):
            value = ", ".join(value) if value else "None"
        optimized_data_lines.append(f"{key}: {value}")
    
    # Combine all lines into a single text string
    optimized_data_text = "\n".join(optimized_data_lines)

    # Save the text representation in session state
    st.session_state.optimized_data_text = optimized_data_text

    # Ensure the 'updated_applicant' directory exists
    directory = "updated_applicant"
    os.makedirs(directory, exist_ok=True)

    # Save the text file in the directory
    file_path = os.path.join(directory, "optimized_resume.txt")
    with open(file_path, "w") as file:
        file.write(optimized_data_text)
