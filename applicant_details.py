import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2
import json
from datetime import datetime
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

class ApplicantDataManager:    
    def __init__(self):
        self.base_dir = "applicants"
        os.makedirs(self.base_dir, exist_ok=True)  # Ensure the directory exists
        print(f"Directory created at: {self.base_dir}")  # Debugging line

    def format_experience(self, experience_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format experience data into a structured dictionary"""
        formatted_experience = []
        for exp in experience_list:
            formatted_exp = {
                "company": exp.get("company", "Not found"),
                "position": exp.get("position", "Not found"),
                "duration": exp.get("duration", "Not found"),
                "job_descriptions": exp.get("job_descriptions", ["Not found"])
            }
            formatted_experience.append(formatted_exp)
        return formatted_experience

    def save_applicant_data(self, data: Dict[str, Any]) -> str:
        """Save applicant data to a JSON file with proper formatting"""
        try:
            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = ''.join(e for e in data['name'] if e.isalnum())
            filename = f"{self.base_dir}/{safe_name}_{timestamp}.json"
            
            print(f"Saving file as: {filename}")  # Debugging line
            
            # Format the data
            formatted_data = {
                "name": data["name"],
                "email": data["email"],
                "mobile": data["mobile"],
                "prof_summary": data["prof_summary"],
                "education": data["education"],
                "experience": self.format_experience(data["experience"]),
                "skills": data["skills"],
                "achievements": data["achievements"],
                "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save the formatted data
            with open(filename, 'w', encoding='utf-8') as f:
                print("Writing data to file...")  # Debugging line
                json.dump(formatted_data, f, indent=4, ensure_ascii=False)
            return filename
        except Exception as e:
            print(f"Error saving data: {str(e)}")  # Debugging line
            st.error(f"Error saving data: {str(e)}")
            return None

# Configure the Generative AI model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# Function to get a response from the model
def get_gemini_response(question, context):
    full_question = f"{context}\n\nQuestion: {question}"
    response = model.generate_content(full_question)
    try:
        return response.text.strip() if response.text.strip() else "Not found"
    except (ValueError, AttributeError):
        return "Not found"

# Function to extract text from PDF using PyPDF2
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

# Functions to extract applicant information
def extract_applicant_name(text):
    return get_gemini_response("What is the Applicant's name? respond 'Not Found' if cannot find", text)

def extract_applicant_email(text):
    return get_gemini_response("What is the Applicant's email? respond 'Not Found' if cannot find", text)

def extract_applicant_mobile(text):
    return get_gemini_response("What is the Applicant's mobile or telephone number? respond 'Not Found' if cannot find", text)

def extract_applicant_education(text):
    question = """
    List the applicant's educational qualifications.
    extract the education point from the content. seperate each other by new line. 
    qualification year institute and everything related to education qualification should be written in single sentense.
    Understand the qualification in total and list each qualification separated by a newline.
    just plain text response.
    """
    response = get_gemini_response(question, text)
    print(response)
    return [edu.strip() for edu in response.splitlines() if edu.strip()] or ["Not found"]

def extract_applicant_experience(text):
    question = """
    list each experience according to each company and position during that time. latest first
    - Company name(not the position) , if cannot find, output as 'Not Found' and separate with newline
    - Position held, work position (not the company) , if cannot find, output as 'Not Found' and separate with newline
    - Duration (e.g., Month Year to Month Year, or current), if cannot find, output as Not Found and separate with newline
    - list job description each point seperated by new line
    Format each experience with these details separated by new line, 
    separate different experience posotions by a double newline.
    plain text output
    exclude the Volunteer or community service experience for this
    follow the output sequence (company name) newline, (position held) newline, (job duration) newline, [job description(each point seperated by new line)] \n\n. 
    if any of these not found, respond not found 
    new line for each experience position and double new line for next experience position is must
    """
    response = get_gemini_response(question, text)
    experience_entries = response.split('\n\n')
    experiences = []

    for entry in experience_entries:
        lines = [line.strip() for line in entry.splitlines() if line.strip()]
        experience_data = {
            "company": lines[0] if len(lines) > 0 else "Not found",
            "position": lines[1] if len(lines) > 1 else "Not found",
            "duration": lines[2] if len(lines) > 2 else "Not found",
            "job_descriptions": [line.lstrip('-').strip() for line in lines[3:]] or ["Not found"]
        }
        experiences.append(experience_data)

    return experiences or [{"company": "Not found", "position": "Not found", "duration": "Not found", "job_descriptions": ["Not found"]}]

def extract_applicant_prof_summary(text):
    return get_gemini_response("Provide the professional summary", text)

def extract_applicant_skills(text):
    """Extract skills from the resume"""
    question = """
    List all technical and professional skills mentioned in the resume.
    Include both hard skills and soft skills.
    do not include achivements, educational qualifications
    dont categorize as technical professional and etc. just output plain text list, with each skill on a new line.
    Do not include bullets or numbers.
    If no skills are found, respond as Not found
    """
    response = get_gemini_response(question, text)
    return [skill.strip() for skill in response.splitlines() if skill.strip()] or ["Not found"]

def extract_special_achievements(text):
    """Extract special achievements from the resume"""
    question = """
    List any special achievements, awards, certifications, or recognition mentioned in the resume.
    Include professional accomplishments and notable results.
    Format as plain text, with each achievement on a new line.
    Do not include bullets or numbers.
    If no special achievements are found, respond with 'Not found'
    """
    response = get_gemini_response(question, text)
    return [achievement.strip() for achievement in response.splitlines() if achievement.strip()] or ["Not found"]

def show_applicant_details():
    st.title("Applicant Details")
    data_manager = ApplicantDataManager()
    
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file is not None:
        pdf_text = extract_text_from_pdf(uploaded_file)

        if pdf_text.strip():
            st.write("Successfully extracted details.")
            # Extract all applicant data
            name = extract_applicant_name(pdf_text)
            email = extract_applicant_email(pdf_text)
            mobile = extract_applicant_mobile(pdf_text)
            education = extract_applicant_education(pdf_text)
            experience = extract_applicant_experience(pdf_text)
            prof_summary = extract_applicant_prof_summary(pdf_text)
            skills = extract_applicant_skills(pdf_text)
            achievements = extract_special_achievements(pdf_text)

            # Start the form context
            with st.form(key="details_form"):
                # Contact Details Section in expander
                with st.expander("Personal Details", expanded=True):
                    name = st.text_input("Name", name)
                    if name in ["Not found", "Unknown"]:
                        st.markdown(f"<p style='color:red;'>Name: {name}</p>", unsafe_allow_html=True)

                    email = st.text_input("Email", email)
                    if email in ["Not found", "Unknown"]:
                        st.markdown(f"<p style='color:red;'>Email: {email}</p>", unsafe_allow_html=True)

                    mobile = st.text_input("Mobile Number", mobile)
                    if mobile in ["Not found", "Unknown"]:
                        st.markdown(f"<p style='color:red;'>Mobile Number: {mobile}</p>", unsafe_allow_html=True)

                # Professional Summary Section in expander
                with st.expander("Professional Summary", expanded=True):
                    prof_summary = st.text_area("Professional Summary", prof_summary)

                # Education Section in expander
                with st.expander("Educational Qualifications", expanded=True):
                    updated_education = []
                    for i, education_item in enumerate(education):
                        updated_education.append(st.text_input(f"Qualification {i + 1}", education_item))

                # Work Experience Section in expander
                with st.expander("Work Experience", expanded=True):
                    updated_experience = []
                    for i, exp in enumerate(experience):
                        st.write(f"### Experience {i + 1}")
                        company = st.text_input(f"Company {i + 1}", exp["company"])
                        position = st.text_input(f"Position {i + 1}", exp["position"])
                        duration = st.text_input(f"Duration {i + 1}", exp["duration"])

                        job_descriptions = []
                        for j, desc in enumerate(exp["job_descriptions"]):
                            job_descriptions.append(st.text_area(
                                f"Job Description {j + 1} for Experience {i + 1}", 
                                desc,
                                height=100
                            ))

                        updated_experience.append({
                            "company": company,
                            "position": position,
                            "duration": duration,
                            "job_descriptions": job_descriptions
                        })

                # Skills Section in expander
                with st.expander("Skills", expanded=True):
                    updated_skills = []
                    for i, skill in enumerate(skills):
                        updated_skills.append(st.text_input(f"Skill {i + 1}", skill))

                # Achievements Section in expander
                with st.expander("Special Achievements", expanded=True):
                    updated_achievements = []
                    for i, achievement in enumerate(achievements):
                        updated_achievements.append(st.text_area(
                            f"Achievement {i + 1}", 
                            achievement,
                            height=100
                        ))

                # Single Submit button at the end of the form
                submit_button = st.form_submit_button("Next →")

                if submit_button:
                    # Validate required fields (you can add more validation as needed)
                    if not name or not email or not mobile:
                        st.error("Please fill in all required fields.")
                    else:
                        # Update applicant data dictionary with all fields
                        applicant_data = {
                            "name": name,
                            "email": email,
                            "mobile": mobile,
                            "prof_summary": prof_summary,
                            "education": updated_education,
                            "experience": updated_experience,
                            "skills": [skill for skill in updated_skills if skill],
                            "achievements": [ach for ach in updated_achievements if ach]
                        }
                        
                        # Save applicant data
                        saved_file = data_manager.save_applicant_data(applicant_data)
                        
                        if saved_file:  # Only update session state if saving was successful
                            # Update session state with all fields
                            st.session_state.update({
                                "name": name,
                                "email": email,
                                "mobile": mobile,
                                "prof_summary": prof_summary,
                                "education": updated_education,
                                "experience": updated_experience,
                                "skills": updated_skills,
                                "achievements": updated_achievements,
                                "applicant_file": saved_file
                            })
                            
                            # Navigate to Job Description page
                            st.session_state.page = "Applicant Personal Details" 
                            st.stop() # Update to navigate to Job Description
                        else:
                            st.error("Failed to save applicant data. Please try again.")

def show_applicant_personal_details():
    """Display and edit the applicant's personal details."""
    st.title("Applicant Personal Details")

    # Extract applicant data from the session state
    pdf_text = st.session_state.pdf_text  # Assuming you stored the extracted PDF text in session state
    name = extract_applicant_name(pdf_text)
    email = extract_applicant_email(pdf_text)
    mobile = extract_applicant_mobile(pdf_text)

    # Start the form context
    with st.form(key="personal_details_form"):
        # Editable fields for personal details
        name = st.text_input("Name", name)
        email = st.text_input("Email", email)
        mobile = st.text_input("Mobile Number", mobile)

        # Submit button
        submit_button = st.form_submit_button("Save Details")

        if submit_button:
            # Update session state with the edited details
            st.session_state.name = name
            st.session_state.email = email
            st.session_state.mobile = mobile
            
            st.success("Personal details saved successfully!")
            # Navigate to the next page or perform any other action
            st.session_state.page = "Professional Summary and Work Experience"  # Change this to the next page you want to navigate to
            st.experimental_rerun()  # Rerun the app to reflect the page change

def show_applicant_professional_summary_and_experience():
    """Display and edit the applicant's professional summary and work experience."""
    st.title("Professional Summary and Work Experience")

    # Extract applicant data from the session state
    pdf_text = st.session_state.pdf_text  # Assuming you stored the extracted PDF text in session state
    prof_summary = extract_applicant_prof_summary(pdf_text)
    experiences = extract_applicant_experience(pdf_text)

    # Start the form context
    with st.form(key="professional_summary_form"):
        # Editable field for professional summary
        st.subheader("Professional Summary")
        prof_summary = st.text_area("Professional Summary", prof_summary)

        # Editable fields for work experience
        st.subheader("Work Experience")
        for i, exp in enumerate(experiences):
            st.write(f"### Experience {i + 1}")
            company = st.text_input(f"Company {i + 1}", exp["company"])
            position = st.text_input(f"Position {i + 1}", exp["position"])
            duration = st.text_input(f"Duration {i + 1}", exp["duration"])
            job_descriptions = st.text_area(f"Job Descriptions for {exp['position']}", "\n".join(exp["job_descriptions"]))

            # Store the updated experience in the session state
            experiences[i] = {
                "company": company,
                "position": position,
                "duration": duration,
                "job_descriptions": job_descriptions.splitlines()  # Convert back to list
            }

        # Submit button
        submit_button = st.form_submit_button("Save and Proceed")

        if submit_button:
            # Update session state with the edited details
            st.session_state.prof_summary = prof_summary
            st.session_state.experience = experiences
            
            st.success("Professional summary and work experience saved successfully!")
            # Navigate to the next page or perform any other action
            st.session_state.page = "Qualifications and Skills"  # Change this to the next page you want to navigate to
            
      # Rerun the app to reflect the page change


