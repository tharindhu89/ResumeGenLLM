import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2
import json
from datetime import datetime

# Load environment variables
load_dotenv()

def initialize_session_variables():
    """
    Initialize session variables if they don't exist.
    """
    if "applicant_data_text" not in st.session_state:
        st.session_state.applicant_data_text = ""  # Initialize as an empty string

initialize_session_variables()

def save_applicant_data_as_text():
    """
    Collects applicant data from session state and saves it as text in session state.
    """
    # Collect data from session state
    applicant_data = {
        "Professional Summary": st.session_state.get("prof_summary", "Not found"),
        "Experience": st.session_state.get("experience", []),
        "Skills": st.session_state.get("skills", ["Not found"]),
        "Special Achievements": st.session_state.get("special_achievements", ["Not found"]),
    }

    # Create a plain text representation of the applicant data
    applicant_data_lines = []
    
    # Loop through the applicant data dictionary
    for key, value in applicant_data.items():
        if isinstance(value, list):
            # Handle experience data (a list of dictionaries)
            if key == "Experience" and isinstance(value, list) and all(isinstance(item, dict) for item in value):
                experience_text = []
                for experience in value:
                    # For each job experience, format the details into a readable text
                    company = experience.get("company", "Not found")
                    position = experience.get("position", "Not found")
                    duration = experience.get("duration", "Not found")
                    job_descriptions = experience.get("job_descriptions", ["Not found"])
                    
                    # Formatting the job descriptions with line breaks and '#'
                    job_desc_text = "\n".join([f"# {desc}" for desc in job_descriptions])
                    
                    # Combine all details for the experience entry
                    experience_details = f"Company: {company}\nPosition: {position}\nDuration: {duration}\n{job_desc_text}"
                    experience_text.append(experience_details)
                
                # Join all experience entries with a double newline
                value = "\n\n".join(experience_text)
            else:
                # For other lists (e.g., Skills, Special Achievements), just join them into a comma-separated string
                value = ", ".join(map(str, value)) if value else "None"

        # Append the formatted text to the list
        applicant_data_lines.append(f"{key}: {value}")

    # Combine all lines into a single text string
    applicant_data_text = "\n".join(applicant_data_lines)

    # Save the text representation in session state
    st.session_state.applicant_data_text = applicant_data_text
    
    # Output the formatted text for debugging or display





def save_applicant_data_to_json():
    """Save applicant data to a JSON file in the applicants directory."""
    # Collect data from session state
    applicant_data = {
        "name": st.session_state.get("name", "Not found"),
        "email": st.session_state.get("email", "Not found"),
        "mobile": st.session_state.get("mobile", "Not found"),
        "professional_summary": st.session_state.get("prof_summary", "Not found"),
        "experience": st.session_state.get("experience", []),
        "skills": st.session_state.get("skills", ["Not found"]),
        "education": st.session_state.get("education", ["Not found"]),
        "special_achievements": st.session_state.get("special_achievements", ["Not found"]),
    }

    # Create the directory if it doesn't exist
    directory = "applicants"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Define the file path with a timestamp
    filename = f"{directory}/applicant_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Write data to a JSON file
    with open(filename, "w") as json_file:
        json.dump(applicant_data, json_file, indent=4)

    # Save the filename in session state
    st.session_state.json_filename = filename  # Store the JSON filename
    
    return filename


# Configure the Generative AI model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

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
    just plain text response. no bulletpoint required
    """
    response = get_gemini_response(question, text)
    print(response)
    return [edu.strip() for edu in response.splitlines() if edu.strip()] or ["Not found"]

def extract_applicant_experience(text):
    question = """
    Please extract the applicant's work experience from the following text. 
    For each job, provide the following details in this exact format:
    Company Name: Company Name Here
    Position: Position Here
    Start Date - End Date: Start Date - End Date or Current Here
    [Description point Here]
    [Description point Here]
    [Description Point Here]

    indicate 'Not Found' if details could not find

    Do not include the square brackets or the text inside them in the output. 
    Each description point should start with a hashtag mark (#).
    Separate each job entry with a double newline. 
    If any of the details are not found, respond with 'Not Found' for that detail.
    Exclude any volunteer or community service experience.
    """
    response = get_gemini_response(question, text)
    print("Raw Response from Model:", response)

    experience_entries = response.split('\n\n')
    experiences = []

    for entry in experience_entries:
        lines = [line.strip() for line in entry.splitlines() if line.strip()]
        experience_data = {
            "company": lines[0].replace("Company Name: ", "").strip() if len(lines) > 0 else "Not found",
            "position": lines[1].replace("Position: ", "").strip() if len(lines) > 1 else "Not found",
            "duration": lines[2].replace("Start Date - End Date: ","").strip() if len(lines) > 2 else "Not found",
            "job_descriptions": []  # Initialize as an empty list
        }

        # Extract job descriptions starting from the fourth line
        if len(lines) > 3:
            # Join all lines after the third line and split by '#' to get individual descriptions
            job_description_text = " ".join(lines[3:])  # Join remaining lines into a single string
            experience_data["job_descriptions"] = [desc.strip() for desc in job_description_text.split('#') if desc.strip()]  # Split by '#' and clean up

        experiences.append(experience_data)
    # Debug: Print the structured experiences
    print("Extracted Experiences:", experiences)

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
    # Clean up each skill by removing dashes and extra whitespace
    return [skill.strip().lstrip('-').strip() for skill in response.splitlines() if skill.strip()] or ["Not found"]

def extract_special_achievements(text):
    """Extract special achievements from the resume."""
    question = """
    Identify any special achievements, awards, certifications, or recognitions mentioned in the resume.
    These should be distinct from skills, job descriptions, or educational qualifications.
    Look for any achievements that are highlighted or emphasized in the text.
    Format the response as plain text, with each achievement on a new line.
    Do not include bullets or numbers.
    If no special achievements are found, respond with 'Not found'.
    """
    response = get_gemini_response(question, text)
    return [achievement.strip() for achievement in response.splitlines() if achievement.strip()] or ["Not found"]

def show_resume_upload_status():
    st.title("Upload Applicant Resume")

    # File uploader for PDF resume
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Extract text from the uploaded PDF
        pdf_text = extract_text_from_pdf(uploaded_file)

        if pdf_text.strip():
            st.success("Resume uploaded successfully!")
            st.write("Extracted Text:")
            st.text_area("Extracted Text", pdf_text, height=300)

            # Store the extracted text in session state
            st.session_state.pdf_text = pdf_text

            # Navigate to the next page after a successful upload
            if st.button("Proceed to Extract details"):
                st.session_state.page = "Applicant Personal Details"  # Change this to the next page you want to navigate to
                  # Rerun the app to reflect the page change
        else:
            st.error("Failed to extract text from the uploaded PDF. Please check the file format.")

def show_applicant_personal_details():
    """Display and edit the applicant's personal details."""
    st.title("Applicant Personal Details")

    # Check if personal details are already in session state
    if "name" not in st.session_state or "email" not in st.session_state or "mobile" not in st.session_state:
        # Extract applicant data from the session state
        pdf_text = st.session_state.pdf_text  # Assuming you stored the extracted PDF text in session state
        st.session_state.name = extract_applicant_name(pdf_text)
        st.session_state.email = extract_applicant_email(pdf_text)
        st.session_state.mobile = extract_applicant_mobile(pdf_text)

    # Start the form context
    with st.form(key="personal_details_form"):
        # Editable fields for personal details
        name = st.text_input("Name", st.session_state.name)
        email = st.text_input("Email", st.session_state.email)
        mobile = st.text_input("Mobile Number", st.session_state.mobile)

        # Submit button
        submit_button = st.form_submit_button("Save and proceed")
        


        if submit_button:
            # Update session state with the edited details
            st.session_state.name = name
            st.session_state.email = email
            st.session_state.mobile = mobile
            
            st.success("Personal details saved successfully!")
            # Navigate to the next page or perform any other action
            st.session_state.page = "Professional Summary and Work Experience"  # Change this to the next page you want to navigate to
    
    if st.button("Back", key="back_to_applicant_data_btn"):
        st.session_state.page = "Applicant Resume Upload"  # Navigate to Applicant Data page        # No need to rerun, Streamlit will automatically re-render the page based on the session state change

def show_applicant_professional_summary_and_experience():
    """Display and edit the applicant's professional summary and work experience."""
    st.title("Professional Summary and Work Experience")

    # Check if professional summary and experiences are already in session state
    if "prof_summary" not in st.session_state or "experience" not in st.session_state:
        # Extract applicant data from the session state
        pdf_text = st.session_state.pdf_text  # Assuming you stored the extracted PDF text in session state
        st.session_state.prof_summary = extract_applicant_prof_summary(pdf_text)
        st.session_state.experience = extract_applicant_experience(pdf_text)

    # Use the values from session state
    prof_summary = st.session_state.prof_summary
    experiences = st.session_state.experience

    # Debug: Print the professional summary
    print("Professional Summary:", prof_summary)

    # Debug: Print the experiences before displaying
    print("Experiences to display:", experiences)
    
    # Start the form context
    with st.form(key="professional_summary_form"):
        # Editable field for professional summary
        st.subheader("Professional Summary")
        prof_summary = st.text_area("Professional Summary", prof_summary)

        # Editable fields for work experience
        st.subheader("Work Experience")
        updated_experiences = []  # Create a new list to hold valid experiences
        for i, exp in enumerate(experiences):
            st.write(f"### Experience {i + 1}")
            company = st.text_input(f"Company {i + 1}", exp["company"], key=f"company_{i}")
            position = st.text_input(f"Position {i + 1}", exp["position"], key=f"position_{i}")
            duration = st.text_input(f"Duration {i + 1}", exp["duration"], key=f"duration_{i}")

            # Use the job_descriptions directly since it's already a list
            with st.expander(f"Job Descriptions for {exp['position']}", expanded=True):
                job_descriptions = []
                for j, desc in enumerate(exp["job_descriptions"]):
                    job_desc_key = f"job_description_{i}_{j}"  # Unique key for each job description text area
                    job_description = st.text_area(f"Job Description {j + 1}", desc.strip(), key=job_desc_key)
                    job_descriptions.append(job_description.strip())  # Collect job descriptions

            # Check if any job description is "Not Found"
            if all(desc != "Not Found" for desc in job_descriptions):
                # Store the updated experience in the new list if valid
                updated_experiences.append({
                    "company": company,
                    "position": position,
                    "duration": duration,
                    "job_descriptions": job_descriptions  # Clean up descriptions
                })

        # Update the session state with valid experiences
        st.session_state.experience = updated_experiences

        # Submit button
        submit_button = st.form_submit_button("Save and Proceed")

        if submit_button:
            # Update session state with the edited details
            st.session_state.prof_summary = prof_summary
            
            st.success("Professional summary and work experience saved successfully!")
            # Navigate to the next page or perform any other action
            st.session_state.page = "Qualifications and Skills"  # Change this to the next page you want to navigate to
            # No need to rerun, Streamlit will automatically re-render the page based on the session state change
    
    if st.button("Back", key="back_to_applicant_personal_data"):
        st.session_state.page = "Applicant Personal Details"
        st.session_state.prof_summary = []
        st.session_state.experience = []  # Navigate to Applicant Data page

def show_applicant_skills_education_achievements():
    """Display the applicant's skills, education, and special achievements."""
    st.title("Qualifications and Skills")

    # Check if skills, education, and achievements are already in session state
    if "skills" not in st.session_state or "education" not in st.session_state or "special_achievements" not in st.session_state:
        # Extract applicant data from the session state
        pdf_text = st.session_state.pdf_text  # Assuming you stored the extracted PDF text in session state
        st.session_state.skills = extract_applicant_skills(pdf_text)
        st.session_state.education = extract_applicant_education(pdf_text)
        st.session_state.special_achievements = extract_special_achievements(pdf_text)

    # Retrieve data from session state
    skills = st.session_state.skills
    education = st.session_state.education
    special_achievements = st.session_state.special_achievements

    # Display Skills
    st.subheader("Skills")
    if skills and skills[0] != "Not found":
        for skill in skills:
            st.write(f"- {skill}")
    else:
        st.write("No skills found.")

    # Display Education
    st.subheader("Education")
    if education and education[0] != "Not found":
        for edu in education:
            st.write(f" {edu}")
    else:
        st.write("No education found.")

    # Display Special Achievements
    st.subheader("Special Achievements")
    if special_achievements and special_achievements[0] != "Not found":
        for achievement in special_achievements:
            st.write(f"- {achievement}")
    else:
        st.write("No special achievements found.")
    
    if st.button("Proceed to Job Descriptions"):
        save_applicant_data_to_json()
        save_applicant_data_as_text()  # Move this inside the button click
        st.session_state.page = "Job Description"

    if st.button("Back", key="back_to_applicant_professional_summary"):
        st.session_state.page = "Professional Summary and Work Experience"
    

