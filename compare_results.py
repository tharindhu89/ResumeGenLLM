from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
from sentence_transformers import SentenceTransformer, util


def jaccard_similarity(text1, text2):
    """Calculate the Jaccard similarity between two texts."""
    # Tokenize the texts into sets of words
    set1 = set(text1.split())
    set2 = set(text2.split())
    
    # Calculate the intersection and union
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    # Calculate Jaccard similarity
    if not union:  # Avoid division by zero
        return 0.0
    return len(intersection) / len(union)

def calculate_sbert_similarity(applicant_text, optimized_text, job_text):
    """Calculate SBERT similarity scores."""
    # Load the SBERT model
    model = SentenceTransformer('all-MiniLM-L6-v2')  

    # Encode the texts
    embeddings = model.encode([applicant_text, optimized_text, job_text], convert_to_tensor=True)

    # Compute cosine similarity
    similarity_matrix = util.cos_sim(embeddings, embeddings).cpu().numpy()

    # Extract individual scores
    applicant_vs_job = similarity_matrix[0, 2]
    optimized_vs_job = similarity_matrix[1, 2]
    applicant_vs_optimized = similarity_matrix[0, 1]

    return applicant_vs_job, optimized_vs_job, applicant_vs_optimized


def load_data_from_session():
    """Load data from session state."""
    try:
        # Debug: Print session state keys
        #st.write("Debug - Available Session State Keys:", list(st.session_state.keys()))
        
        # Get original data
        original_skills = st.session_state.get("skills", [])
        original_points = []
        for exp in st.session_state.get("experience", []):
            if exp and "job_descriptions" in exp:
                original_points.extend(exp["job_descriptions"])
        original_summary = st.session_state.get("Professional Summary", "")
        
        # Get optimized data
        updated_skills = st.session_state.get("updated_skills", [])
        optimized_points = []
        for exp in st.session_state.get("updated_experience", []):
            if exp and "job_descriptions" in exp:
                optimized_points.extend(exp["job_descriptions"])
        generated_summary = st.session_state.get("generated_prof_summary", "")
        
        # Get job data
        job_responsibilities = st.session_state.get("job_responsibilities", [])
        special_skills = st.session_state.get("special_skills", [])
        requirements = st.session_state.get("requirements", [])
        
        # Debug: Print raw data
        #st.write("Debug - Raw Data:")
        #st.write("Original Skills:", original_skills)
        #st.write("Original Points:", original_points)
        #st.write("Original Summary:", original_summary)
        #st.write("Updated Skills:", updated_skills)
        #st.write("Optimized Points:", optimized_points)
        #st.write("Generated Summary:", generated_summary)
        #st.write("Job Responsibilities:", job_responsibilities)
        #st.write("Special Skills:", special_skills)
        #st.write("Requirements:", requirements)
        
        # Create text strings
        applicant_text = f"""
        Professional Summary: {original_summary}
        Skills: {' | '.join(original_skills)}
        Experience Points: {' | '.join(original_points)}
        """.strip()
        
        optimized_text = f"""
        Professional Summary: {generated_summary}
        Skills: {' | '.join(updated_skills)}
        Experience Points: {' | '.join(optimized_points)}
        """.strip()
        
        job_text = f"""
        Job Responsibilities: {' | '.join(job_responsibilities)}
        Required Skills: {' | '.join(special_skills)}
        Requirements: {' | '.join(requirements)}
        """.strip()
        
        # Validate output
        if not applicant_text.strip():
            st.error("No original text could be generated")
            return None, None, None
        if not optimized_text.strip():
            st.error("No optimized text could be generated")
            return None, None, None
        if not job_text.strip():
            st.error("No job text could be generated")
            return None, None, None
            
        return applicant_text.strip(), optimized_text.strip(), job_text.strip()
        
    except Exception as e:
        st.error(f"Error in load_data_from_session: {str(e)}")
        st.write("Debug - Error Details:", {
            "Error Type": type(e).__name__,
            "Error Message": str(e)
        })
        return None, None, None

def show_similarity():
    """Calculate and display similarity scores."""
    st.title("Resume Optimization Analysis")
    
    try:
        # Load and validate data
        applicant_text, optimized_text, job_text = load_data_from_session()
        
        if not all([applicant_text, optimized_text, job_text]):
            st.error("Failed to load required data")
            return
        
        # Debug: Display texts
        st.subheader("Debug - Text Content:")
        with st.expander("Show Text Content"):
            st.write("Original Content:", applicant_text)
            st.write("Optimized Content:", optimized_text)
            st.write("Job Content:", job_text)
        
        # Calculate similarity
        vectorizer = CountVectorizer()
        vectors = vectorizer.fit_transform([applicant_text, optimized_text, job_text])
        
        # Debug: Show vectorizer details
        st.write("Debug - Vectorizer Features:", len(vectorizer.get_feature_names_out()))
        
        similarity_matrix = cosine_similarity(vectors)
        
        # Debug: Show similarity matrix
        st.write("Debug - Similarity Matrix:", similarity_matrix)
        
        # Calculate and display scores
        applicant_vs_job = similarity_matrix[0][2]
        optimized_vs_job = similarity_matrix[1][2]
        applicant_vs_optimized = similarity_matrix[0][1]
        
        st.subheader("Similarity Analysis")
        st.write("**Cosine Similarity Scores:**")
        st.write(f"- Original Content vs Job Requirements: {applicant_vs_job:.2%}")
        st.write(f"- Optimized Content vs Job Requirements: {optimized_vs_job:.2%}")
        st.write(f"- Original vs Optimized Content: {applicant_vs_optimized:.2%}")

        # Save similarity scores in session state
        st.session_state.cosine_applicant_vs_job = applicant_vs_job
        st.session_state.cosine_optimized_vs_job = optimized_vs_job
        st.session_state.cosine_applicant_vs_optimized = applicant_vs_optimized
        
        improvement = optimized_vs_job - applicant_vs_job
        if improvement > 0:
            st.success(f"Optimization improved job match by {improvement:.2%}")
        else:
            st.warning(f"Optimization changed job match by {improvement:.2%}")
        
    except Exception as e:
        st.error(f"Error in show_similarity: {str(e)}")
        st.write("Debug - Error Details:", {
            "Error Type": type(e).__name__,
            "Error Message": str(e)
        })
    
    """Display similarity scores using SBERT."""
    st.title("SBERT Resume Optimization Analysis")
    
    # Load data
    applicant_text, optimized_text, job_text = load_data_from_session()
    if not all([applicant_text, optimized_text, job_text]):
        st.error("Failed to load required data")
        return

    # Calculate SBERT similarity
    sbert_applicant_vs_job, sbert_optimized_vs_job, sbert_applicant_vs_optimized = calculate_sbert_similarity(
        applicant_text, optimized_text, job_text
    )
    
    # Display similarity scores
    st.subheader("SBERT Similarity Analysis")
    st.write("**Cosine Similarity Scores:**")
    st.write(f"- Original Content vs Job Requirements: {sbert_applicant_vs_job:.2%}")
    st.write(f"- Optimized Content vs Job Requirements: {sbert_optimized_vs_job:.2%}")
    st.write(f"- Original vs Optimized Content: {sbert_applicant_vs_optimized:.2%}")

    st.session_state.sbert_applicant_vs_job = sbert_applicant_vs_job
    st.session_state.sbert_optimized_vs_job = sbert_optimized_vs_job
    st.session_state.sbert_applicant_vs_optimized = sbert_applicant_vs_optimized
    
    improvement = optimized_vs_job - applicant_vs_job
    if improvement > 0:
        st.success(f"Optimization improved job match by {improvement:.2%}")
    else:
        st.warning(f"Optimization changed job match by {improvement:.2%}")


    """Display Jaccard similarity results for three texts."""
    jaccard_applicant_optimized = jaccard_similarity(applicant_text, optimized_text)
    jaccard_applicant_job = jaccard_similarity(applicant_text, job_text)
    jaccard_optimized_job = jaccard_similarity(optimized_text, job_text)

    st.subheader("Jaccard Similarity Results")
    st.write(f"**Applicant vs Optimized:** {jaccard_applicant_optimized:.2%}")
    st.write(f"**Applicant vs Job Requirements:** {jaccard_applicant_job:.2%}")
    st.write(f"**Optimized vs Job Requirements:** {jaccard_optimized_job:.2%}")

    st.session_state.jaccard_applicant_vs_job = jaccard_applicant_optimized
    st.session_state.jaccard_optimized_vs_job = jaccard_applicant_job
    st.session_state.jaccard_applicant_vs_optimized = jaccard_optimized_job

    if st.button("word similarity"):
        st.session_state.page = "word similarity"