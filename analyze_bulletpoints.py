import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

def find_most_similar_responsibility(original_point, job_responsibilities):
    """Find the job responsibility that is most similar to the original point."""
    # Ensure original_point is a string
    if isinstance(original_point, list):
        original_point = " ".join(original_point)  # Join list into a single string

    # Initialize the vectorizer
    vectorizer = CountVectorizer()

    # Vectorize the original point
    original_vector = vectorizer.fit_transform([original_point])

    # Vectorize the job responsibilities
    job_vectors = vectorizer.transform(job_responsibilities)

    # Calculate cosine similarity between the original point and job responsibilities
    similarities = cosine_similarity(original_vector, job_vectors)

    # Find the index of the highest similarity score
    highest_similarity_index = similarities[0].argmax()
    st.write(highest_similarity_index)
    most_similar_responsibility = job_responsibilities[highest_similarity_index]
    st.write(most_similar_responsibility)
    return most_similar_responsibility

# Load the SBERT mode
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')



# Configure the Generative AI model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def save_data_entry(original_point, similar_responsibility, optimized_point, sbert_model):
    """Save original point, similar responsibility, optimized point, and similarity scores as a data entry."""
    
    if "data_entries" not in st.session_state:
        st.session_state.data_entries = []

    # Compute similarity scores
    original_vs_similar = util.cos_sim(
        sbert_model.encode(original_point, convert_to_tensor=True),
        sbert_model.encode(similar_responsibility, convert_to_tensor=True)
    ).item()

    original_vs_optimized = util.cos_sim(
        sbert_model.encode(original_point, convert_to_tensor=True),
        sbert_model.encode(optimized_point, convert_to_tensor=True)
    ).item()

    similar_vs_optimized = util.cos_sim(
        sbert_model.encode(similar_responsibility, convert_to_tensor=True),
        sbert_model.encode(optimized_point, convert_to_tensor=True)
    ).item()

    # Create a dictionary for the data entry
    entry = {
        "Original Point": original_point,
        "Similar Responsibility": similar_responsibility,
        "Optimized Point": optimized_point,
        "Similarity: Original vs Similar": round(original_vs_similar, 4),
        "Similarity: Original vs Optimized": round(original_vs_optimized, 4),
        "Similarity: Similar vs Optimized": round(similar_vs_optimized, 4)
    }

    # Append the entry to the session state list
    st.session_state.data_entries.append(entry)

    # Define the file path for the CSV
    file_path = "similarity.csv"

    # Check if the CSV file already exists
    if os.path.exists(file_path):
        # If the file exists, read the existing data
        df = pd.read_csv(file_path)
        # Concatenate the new entry to the dataframe
        new_entry_df = pd.DataFrame([entry])  # Convert entry to DataFrame
        df = pd.concat([df, new_entry_df], ignore_index=True)  # Concatenate the new entry
    else:
        # If the file does not exist, create a new dataframe with the entry
        df = pd.DataFrame([entry])

    # Save the combined data (existing + new entries) back to the CSV file
    df.to_csv(file_path, index=False)

def get_gemini_response(question, context):
    """Get a response from the Generative AI model."""
    full_question = f"{context}\n\nQuestion: {question}"
    response = model.generate_content(full_question)
    try:
        return response.text.strip() if response.text.strip() else "Not found"
    except (ValueError, AttributeError):
        return "Not found"

def extract_relevant_skills(job_description_point):
    """Extract relevant skills using only updated skills without modifying the original list."""
    
    # Get skills from session state
    skills = st.session_state.get("skills", []) + st.session_state.get("updated_skills", [])  # Combine saved skills with updated skills
    relevant_skills_list = []
    
    context = f"""
    Job Description Point: {job_description_point}
    Available Skills: {', '.join(skills)}
    
    Instructions:
    1. Select 2 most relevant skills from Available Skills.
    2. Skills must directly relate to this specific point.
    3. Avoid unrelated or generic skills.
    """
    
    question = """
    Identify the 2 most relevant technical skills from the Available Skills list.
    Output exactly 2 skills, separated by commas.
    If no unique skills match, output 'NOT FOUND'.
    """
    
    relevant_skills = get_gemini_response(question, context)
    
    if relevant_skills != "NOT FOUND":
        skills_list = [skill.strip() for skill in relevant_skills.split(",")]
        valid_skills = [s for s in skills_list if s in skills][:2]  # Limit to 2 skills
        if len(valid_skills) == 2:
            relevant_skills_list.append(valid_skills)
        else:
            relevant_skills_list.append(["NOT FOUND", "NOT FOUND"])  # Ensure two entries
    else:
        relevant_skills_list.append(["NOT FOUND", "NOT FOUND"])  # Ensure two entries
    
    return relevant_skills_list

def generate_optimized_point(original_point, similar_responsibilities, relevant_skills):
    """Generate an optimized job experience point based on the original point, responsibilities, and skills."""
    
    context = f"""
    Original Experience: {original_point}
    Target Job Requirement: {similar_responsibilities}
    Relevant Skills: {relevant_skills}
    """
    
    optimize_question = """
     Analyze the original point
     Identify key actions
     Incorporate keywords from Target Job Requirement
     Start with a strong action verb
     Maintain the original experience meaning and quantifiable achievements
     do not include specific locations names from similar responsibility 
     always keep Original Experience meaning or context
     Incorporating mentioned 'relevant skills' where relevant
     Maintaining any metrics or achievements from the original
     Keep it concise and impactful
     Output just the optimized sentence without any prefixes or explanations.
    """
    
    optimized_point = get_gemini_response(optimize_question, context)
    
    # Clean up the response
    optimized_point = optimized_point.strip()
    
    # Ensure it starts with an action verb
    if optimized_point and not optimized_point[0].isalpha():
        optimized_point = optimized_point.lstrip('•-* ')
    
    return optimized_point

def batch_search_similar_job_responsibilities(points, job_responsibilities):
    """Match applicant's experience points with relevant job responsibilities."""
    similar_responsibilities_list = []
    used_responsibilities = set()  # Track used responsibilities

    for original_point in points:
        # Filter out already used responsibilities
        available_responsibilities = [r for r in job_responsibilities if r not in used_responsibilities]
        
        # If no unused responsibilities are available, use all responsibilities
        if not available_responsibilities:
            st.warning("All job responsibilities have been used. Using full list again.")
            available_responsibilities = job_responsibilities
        
        context = f"""
        Applicant's Experience: {original_point}
        Available Job Requirements: {' | '.join(available_responsibilities)}
        Previously Used Requirements: {' | '.join(used_responsibilities)}
        
        Instructions:
        1. Select the single most relevant requirement that hasn't been used before
        2. The requirement must closely match the meaning of the original point
        3. Do not modify or rephrase the requirement
        4. Return exactly as it appears in the Available Job Requirements list
        5. Avoid requirements that express similar ideas to those previously used
        """
        
        question = """
        From the Available Job Requirements list, return the single most relevant and unique responsibility 
        that best matches the original point while being different from previously used requirements.
        Copy and paste the exact requirement from the list.
        """

        similar_responsibility = get_gemini_response(question, context)
        
        if similar_responsibility in available_responsibilities:
            similar_responsibilities_list.append([similar_responsibility])
            used_responsibilities.add(similar_responsibility)
        else:
            # If no match, find the most different unused responsibility
            for resp in available_responsibilities:
                if resp not in used_responsibilities:
                    similar_responsibilities_list.append([resp])
                    used_responsibilities.add(resp)
                    break

    return similar_responsibilities_list

def show_analyze_bp():
    st.title("Analyze and Optimize Applicant Experience")
    
    experiences = st.session_state.get("experience", [])
    skills = st.session_state.get("skills", []) + st.session_state.get("updated_skills", [])  # Combine saved skills with updated skills
    #st.write(skills)
    
    # Check if applicant data is available
    if not experiences:
        st.write("No applicant experience data found.")
        return

    job_description = st.session_state.get("job_description", "Not found")
    job_responsibilities = st.session_state.get("job_responsibilities", [])

    if job_description == "Not found":
        st.write("Job description not found.")
        return

    # Initialize current experience index in session state
    if "current_experience_index" not in st.session_state:
        st.session_state.current_experience_index = 0

    # Initialize optimized points in session state if not already done
    if "optimized_points" not in st.session_state:
        st.session_state.optimized_points = {}

    # Display current experience
    current_index = st.session_state.current_experience_index
    current_experience = experiences[current_index]

    st.subheader(f"**{current_experience['company']} - {current_experience['position']} ({current_experience['duration']})**")

    original_points = current_experience.get("job_descriptions", [])
    
    # Check if optimized points for the current experience already exist
    if current_index in st.session_state.optimized_points:
        optimized_points = st.session_state.optimized_points[current_index]
    else:
        optimized_points = []

        if original_points:
            # Clean the job responsibilities before using them
            cleaned_job_responsibilities = []
            for resp in job_responsibilities:
                cleaned_resp = resp.lstrip("•- *")  # Remove common bullet point characters
                cleaned_resp = ''.join(e for e in cleaned_resp if e.isalnum() or e.isspace())  # Remove unwanted symbols
                cleaned_job_responsibilities.append(cleaned_resp.strip())

            # Save cleaned job responsibilities back to session state
            st.session_state.job_responsibilities = cleaned_job_responsibilities

            # Iterate over each original point to find similar responsibilities
            for idx, point in enumerate(original_points):
                if not point.strip():
                    continue
                st.write(f"**Original Point:** {point}")

                # Find the most similar job responsibility for the current original point
                most_similar_responsibility = find_most_similar_responsibility(point, cleaned_job_responsibilities)
                
                # Get current skills for this point
                current_skills = extract_relevant_skills(point)  # Extract skills for the current point
                
                # Generate optimized point using the original point, similar responsibility, and current skills
                optimized_point = generate_optimized_point(point, most_similar_responsibility, current_skills)

                # Add the optimized point to the list
                optimized_points.append(optimized_point)

                # Save data entry if needed
                save_data_entry(
                    original_point=point,
                    similar_responsibility=most_similar_responsibility,
                    optimized_point=optimized_point,
                    sbert_model=sbert_model
                )

                # Prepare table data for the current point
                table_data = {
                    "Original Point": [point],
                    "Relevant Job Responsibility": [most_similar_responsibility],
                    "Relevant Skills": ", ".join([skill for sublist in current_skills for skill in sublist])  # Flatten the list of lists
                }
                df = pd.DataFrame(table_data)
                st.table(df)

                st.write("**Optimized Experience Point:**")
                st.write(optimized_point)

            # Create updated experience entry with the optimized points
            updated_experience = {
                "company": current_experience["company"],
                "position": current_experience["position"],
                "duration": current_experience["duration"],
                "original_descriptions": original_points,
                "job_descriptions": optimized_points  # Store the optimized points
            }
            
            # Initialize updated_experience list in session state if it doesn't exist
            if "updated_experience" not in st.session_state:
                st.session_state.updated_experience = []
            
            # Ensure the updated_experience list has enough slots
            while len(st.session_state.updated_experience) <= current_index:
                st.session_state.updated_experience.append({})
            
            # Update the specific experience
            st.session_state.updated_experience[current_index] = updated_experience

            # Store optimized points in session state
            st.session_state.optimized_points[current_index] = optimized_points

            # Display all optimized points for the current experience
            st.write("### Optimized Points for This Experience")
            for idx, opt_point in enumerate(optimized_points):
                st.write(f"{idx + 1}. {opt_point}")

    # Navigation button for next job experience
    if st.button("Next Experience"):
        if current_index < len(experiences) - 1:
            st.session_state.current_experience_index += 1  # Increment index to show next experience
        else:
            # If it's the last experience, navigate to Professional Experience page
            st.session_state.page = "Professional Experience"  # Change to the Professional Experience page

    # Final summary message after all experiences
    st.write("You have reviewed and optimized all experience points. Thank you!")
    # Button to navigate to the Professional Experience page
    if st.button("Go to Professional Experience"):
        st.session_state.page = "Professional Experience"  # Change to the Professional Experience page
  