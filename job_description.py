import streamlit as st
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import google.generativeai as genai
from keybert import KeyBERT
from rake_nltk import Rake


load_dotenv()

def extract_key_words_rake(job_description):
    rake = Rake()

# Extract keywords
    rake.extract_keywords_from_text(job_description)
    keywords = rake.get_ranked_phrases()
    return(keywords)

def extract_key_words_keybert(job_description):
    model = KeyBERT('all-MiniLM-L6-v2')

# Extract keywords
    keywords = model.extract_keywords(job_description, keyphrase_ngram_range=(1, 2), top_n=10)
    return(keywords)

def save_job_description_as_text():
    """
    Collects job description data from session state and saves it as text in session state.
    """
    # Collect data from session state
    job_data = {
        "Required Qualifications": st.session_state.get("required_qualifications", ["Not found"]),
        "Special Skills": st.session_state.get("special_skills", ["Not found"]),
        "Job Responsibilities": st.session_state.get("job_responsibilities", ["Not found"]),
    }

    # Create a plain text representation of the job description data
    job_data_lines = []

    # Loop through the job data dictionary
    for key, value in job_data.items():
        if isinstance(value, list):
            # For lists like qualifications, skills, and responsibilities, join them into a string with new lines
            value = "\n".join([f"- {item}" for item in value])

        # Append the formatted text to the list
        job_data_lines.append(f"{key}:\n{value}")

    # Combine all lines into a single text string
    job_data_text = "\n\n".join(job_data_lines)

    # Save the text representation in session state
    st.session_state.job_description_text = job_data_text

    # Output the formatted text for debugging or display (optional)
    st.write(job_data_text)

    # Optionally, you can show a success message
    st.success("Job description data saved as text in session state")



genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# Create directory for saving job descriptions
JOB_DATA_DIR = "job_descriptions"
os.makedirs(JOB_DATA_DIR, exist_ok=True)

def get_gemini_response(question, context):
    full_question = f"{context}\n\nQuestion: {question}"
    response = model.generate_content(full_question)
    try:
        return response.text.strip() if response.text.strip() else "Not found"
    except (ValueError, AttributeError):
        return "Not found"



def extract_job_details(job_description):
    """Extract company name, position, and location from job description"""
    company_name = get_gemini_response("What is the company name from the job description?", job_description)
    position = get_gemini_response("What is the position title from the job description?", job_description)
    location = get_gemini_response("What is the job location from the job description?", job_description)
    return company_name, position, location

def extract_required_qualifications(job_description):
    """Extract required qualifications from job description"""
    question = """
    List the required qualifications for the applicant as stated in the job description.
    plain text and no need of bulletpoints
    Format the response as plain text, separating each qualification by a newline.
    """
    response = get_gemini_response(question, job_description)
    # Return qualifications as a list
    return [qual.strip() for qual in response.splitlines() if qual.strip()] or ["Not found"]

def extract_special_skills(job_description):
    """Extract special skills and keywords from job description"""
    question = """
    Identify the special skills and keywords mentioned in the job description, output the technical keywords that 
    has an effect on submitting an application.
    get only the skills required for the job mentioned in job description
    plain text without bulletpoints and categorising as Responsibilities, Requirements and Qualifications
    response as plain text stream, separating each skill or keyword with '#'
    """
    response = get_gemini_response(question, job_description)
   # Split the response based on '#' and return as a list
    skills = [skill.strip() for skill in response.split('#') if skill.strip()]
    
    # If no skills are found, return a default value
    return skills if skills else ["Not found"]

def extract_job_responsibilities(job_description):
    """Extract job responsibilities from job description"""
    question = """
    List all job responsibilities and requirements mentioned in the job description.
    Output as plain text with each item on a new line.
    Do not use any bullets, numbers, or category labels.
    Do not divide into sections or categories.
    Do not use special characters.
    """
    response = get_gemini_response(question, job_description)
    
    # Clean and split the response into a list, removing any empty lines
    responsibilities = [
        line.strip() 
        for line in response.splitlines() 
        if line.strip() and 
        not line.startswith(('Responsibilities:', 'Requirements:', 'Qualifications:'))
    ]
    
    return responsibilities if responsibilities else ["Not found"]

def save_job_data(job_data):
    """
    Save job data to a JSON file and store the filename in the session state.
    """
    try:
        # Generate a safe filename using the company name and position
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = ''.join(e for e in job_data['company_name'] if e.isalnum())
        safe_position = ''.join(e for e in job_data['position'] if e.isalnum())
        filename = f"{JOB_DATA_DIR}/{safe_company}_{safe_position}_{timestamp}.json"
        
        # Add submission date to job data
        job_data['submission_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        """" # Save the job data to a JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=4, ensure_ascii=False)"""
        
        with open(filename, "w") as json_file:
            json.dump(job_data, json_file, indent=4)
        
        # Store the filename in the session state
        st.session_state.job_description_filename = filename
        
        st.success(f"Job data saved successfully: {filename}")
        return filename
    
    except Exception as e:
        st.error(f"Error saving job data: {str(e)}")
        return None

def show_job_description_input():
    """Function to show the job description input form."""
    st.title("Job Description Input")

    # Initialize session state for job description
    if "job_description" not in st.session_state:
        st.session_state.job_description = ""

    # Check if details have been extracted
    if "extracted" not in st.session_state:
        st.session_state.extracted = False

    # If details have not been extracted, show the form
    if not st.session_state.extracted:
        with st.form(key="job_description_form"):
            job_description = st.text_area(
                "Paste Job Description Here:", 
                value=st.session_state.job_description,
                height=300,
                key="job_desc_input"
            )

            # Create Submit button
            submit_button = st.form_submit_button("Extract Details")

            if submit_button and job_description:
                # Extract all job details
                company_name, position, location = extract_job_details(job_description)
                required_qualifications = extract_required_qualifications(job_description)
                special_skills = extract_special_skills(job_description)
                job_responsibilities = extract_job_responsibilities(job_description)

                # Extract keywords using Rake and KeyBERT
                st.session_state.rake_keywords = extract_key_words_rake(job_description)
                st.session_state.keybert_keywords = extract_key_words_keybert(job_description)

                # Prepare job data
                job_data = {
                    "job_description": job_description,
                    "company_name": company_name,
                    "position": position,
                    "location": location,
                    "required_qualifications": required_qualifications,
                    "special_skills": special_skills,
                    "job_responsibilities": job_responsibilities,
                }

                # Create a plain text representation of the job data
                selected_job_data = {
                    "Required Qualifications": required_qualifications,
                    "Special Skills": special_skills,
                    "Job Responsibilities": job_responsibilities,
                }

                job_data_lines = []
                for key, value in selected_job_data.items():
                    if isinstance(value, list):
                        value = ", ".join(value) if value else "None"
                        job_data_lines.append(f"{key}: {value}")

                # Combine all lines into a single text string
                job_data_text = "\n".join(job_data_lines)

                # Save the text representation in session state
                st.session_state.selected_job_data_string = job_data_text

                # Ensure the 'job_descriptions' directory exists
                directory = "job_descriptions"
                os.makedirs(directory, exist_ok=True)

                # Save the text file in the directory
                file_path = os.path.join(directory, "job_description.txt")
                with open(file_path, "w") as file:
                    file.write(job_data_text)

                saved_file = save_job_data(job_data)
                if saved_file:
                    st.success(f"Job data saved successfully to {saved_file}")

                # Save to session state
                st.session_state.update(job_data)
                st.session_state.extracted = True  # Mark as extracted

    # Add navigation buttons (Back and Proceed)
    col1, col2 = st.columns([1, 1])  # Split space for Back and Submit buttons

    with col1:
        # Back button to go back to the previous page (e.g., Applicant Data page)
        if st.button("Back", key="back_to_applicant_skills_btn"):
            st.session_state.extracted = False 
            st.session_state.page = "Qualifications and Skills"  # Navigate to Applicant Data page
            

    with col2:
        # Proceed button to go to the next page (e.g., Skills Management page)
        if st.button("Proceed", key="proceed_to_skills_management_btn"):
            st.session_state.page = "Skills Management"  # Navigate to Skills Management page          
        

def show_extracted_job_details():
    """Function to display the extracted job details."""
    st.subheader("Extracted Job Details")
    st.write(f"**Company Name:** {st.session_state.company_name}")
    st.write(f"**Position:** {st.session_state.position}")
    st.write(f"**Location:** {st.session_state.location}")

    st.subheader("Required Qualifications")
    # Display qualifications as a list
    for qualification in st.session_state.required_qualifications:
        st.write(f"- {qualification}")

    st.subheader("Special Skills")
    # Display skills as a list
    for skill in st.session_state.special_skills:
        st.write(f"- {skill}")

    st.subheader("Job Responsibilities")
    # Display responsibilities as a list
    for responsibility in st.session_state.job_responsibilities:
        st.write(f"- {responsibility}")

    # Display extracted keywords from Rake and KeyBERT
    #st.subheader("Extracted Keywords")
    #st.write("**Rake Keywords:**")
    #if "rake_keywords" in st.session_state:
    #    for keyword in st.session_state.rake_keywords:
    #        st.write(f"- {keyword}")
    #else:
    #    st.write("No Rake keywords found.")

    #st.write("**KeyBERT Keywords:**")
    #if "keybert_keywords" in st.session_state:
    #    for keyword in st.session_state.keybert_keywords:
     #       st.write(f"- {keyword}")
    #else:
     #   st.write("No KeyBERT keywords found.")

    # Add navigation buttons (Back and Proceed)
    col1, col2 = st.columns([1, 1])  # Split space for Back and Submit buttons

    with col1:
        # Back button to go back to the previous page (e.g., Applicant Data page)
        if st.button("Back", key="back_to_applicant_skills_btn"):
            st.session_state.extracted = False
            st.session_state.page = "Job Description"  # Navigate to Applicant Data page

    with col2:
        # Proceed button to go to the next page (e.g., Skills Management page)
        if st.button("Proceed", key="proceed_to_skills_management_btn"):
            st.session_state.page = "Skills Management"  # Navigate to Skills Management page 


def show_job_description():
    """Main function to control the job description flow."""
    
    # Initialize session state variables if not already set
    if "extracted" not in st.session_state:
        st.session_state.extracted = False
    if "job_description" not in st.session_state:
        st.session_state.job_description = ""
    if st.session_state.extracted:
        show_extracted_job_details()
    else:
        show_job_description_input()
        

        
