import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the Generative AI model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def get_gemini_response(question, context):
    """Get a response from the Generative AI model."""
    full_question = f"{context}\n\nQuestion: {question}"
    response = model.generate_content(full_question)
    try:
        return response.text.strip() if response.text.strip() else "Not found"
    except (ValueError, AttributeError):
        return "Not found"

def generate_professional_summary(applicant_data, job_description):
    """Generate a professional summary based on applicant data and job description."""
    try:
        # Get education
        qualifications = ", ".join(applicant_data.get("education", []))
        
        # Get special achievements
        achievements = ", ".join(applicant_data.get("special_achievements", []))
        
        # Get updated skills
        skills = st.session_state.get("final_skills", []) or st.session_state.get("updated_skills", [])
        skills_str = ", ".join(skills)
        
        # Get job descriptions from updated experience
        optimized_points = []
        if "updated_experience" in st.session_state:
            for exp in st.session_state.updated_experience:
                if exp and isinstance(exp, dict):
                    # Get job descriptions from the experience dictionary
                    descriptions = exp.get('job_descriptions', [])
                    if descriptions:
                        optimized_points.extend(descriptions)
        
        # Debug information
        #st.write("Debug - Experience Data:")
        #st.write("Updated Experience Structure:")
        #for exp in st.session_state.get("updated_experience", []):
        #    if exp:
        #       st.write(f"Company: {exp.get('company')}")
        #        st.write(f"Position: {exp.get('position')}")
        #        st.write(f"Job Descriptions: {exp.get('job_descriptions', [])}")
        #st.write("Total Optimized Points:", len(optimized_points))
        
        # Validate we have necessary data
        if not optimized_points:
            st.error("No job descriptions found in updated experience. Please complete the experience optimization step first.")
            return "Please optimize your experience points before generating the summary."
        
        # Filter out empty strings and join points
        experience_str = " | ".join(filter(None, optimized_points))

        context = f"""
        Create a professional summary using the following components:
        
        Qualifications: {qualifications}
        Updated Skills: {skills_str}
        Key Achievements: {achievements}
        Experience Points: {experience_str}
        Target Job Description: {job_description}
        
        Instructions:
        
        Emphasize the updated skills that match the job description
        Highlight key experience points matches job description
        Include relevant achievements and qualifications
        Ensure alignment with the target job description
        Make it concise and impactful 
        Use strong action verbs
        do not include new content, names, industries
        do not use me, i , my , our etc
        """
        
        question = """
        Generate a professional summary that showcases the candidate's expertise, 
        emphasizing updated skills, experience, education, achivements while aligning with the job requirements.
        write 150 word summary one paragrpah.
        """
        
        summary = get_gemini_response(question, context)
        
        if summary == "Not found":
            st.error("Failed to generate summary. Please try again.")
            return "Unable to generate summary. Please try again."
            
        return summary
        
    except Exception as e:
        st.error(f"Error in generate_professional_summary: {str(e)}")
        st.write("Debug - Error Details:", {
            "Error Type": type(e).__name__,
            "Error Message": str(e)
        })
        return "Error generating summary. Please try again."

def Show_professional_experience():
    st.title("Professional Experience")
    
    # Debug: Print session state keys
    #st.write("Debug - Session State Keys:", list(st.session_state.keys()))
    
    # Check if required data is in session state
    required_keys = ["name", "experience", "education", "skills", "special_achievements"]
    missing_keys = [key for key in required_keys if key not in st.session_state]
    
    if missing_keys:
        st.error(f"Missing required data: {', '.join(missing_keys)}")
        return
    
    try:
        # Create applicant data dictionary
        applicant_data = {
            "education": st.session_state.education,
            "experience": st.session_state.updated_experience,
            "skills": st.session_state.updated_skills,
            "special_achievements": st.session_state.special_achievements,
        }
        
        # Debug: Print applicant data
        #st.write("Debug - Applicant Data:", applicant_data)
        
        job_description = st.session_state.get("job_description", "")
        #st.write(job_description)
        if not job_description:
            st.warning("Job description is empty")
        
        # Debug: Print experience data
        #st.write("Debug - Experience Data:")
        #for exp in applicant_data["experience"]:
        #    st.write(f"Company: {exp.get('company')}")
        #    st.write(f"Optimized Points: {exp.get('job_descriptions', [])}")
        
        # Generate the professional summary
        if "generated_prof_summary" not in st.session_state:
            st.info("Generating professional summary...")
            try:
                summary = generate_professional_summary(applicant_data, job_description)
                st.session_state.generated_prof_summary = summary
                st.success("Summary generated successfully")
            except Exception as e:
                st.error(f"Error generating summary: {str(e)}")
                return

        st.subheader("Generated Professional Summary")
        st.write(st.session_state.generated_prof_summary)

        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Regenerate Summary"):
                del st.session_state.generated_prof_summary
                st.rerun()
        with col2:
            if st.button("Preview Resume"):
                st.session_state.page = "Preview Resume"
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Debug - Error Details:", {
            "Error Type": type(e).__name__,
            "Error Message": str(e)
        })
