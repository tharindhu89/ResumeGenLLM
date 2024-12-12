from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import TruncatedSVD
import streamlit as st
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import re
from final_results import save_session_data_to_csv

nltk.download('stopwords')

def clean_and_process_text(text):
    """Clean the text by removing stop words, symbols, and special characters, and return the base words."""
    # Initialize the stemmer
    stemmer = PorterStemmer()
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove symbols and special characters
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Split the text into words
    words = text.split()
    
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    cleaned_words = [stemmer.stem(word) for word in words if word not in stop_words]
    
    return set(cleaned_words)  # Return as a set for easy comparison

def count_similar_words(text1, text2):
    """Count the number of similar words between two cleaned texts."""
    # Clean and process both texts
    words1 = clean_and_process_text(text1)
    words2 = clean_and_process_text(text2)
    
    # Find common words
    common_words = words1.intersection(words2)
    
    # Return the count of common words
    return len(common_words)

def load_data_from_session():
    """Load data from session state."""
    try:
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
        """.strip()
        
        return applicant_text.strip(), optimized_text.strip(), job_text.strip()
        
    except Exception as e:
        st.error(f"Error in load_data_from_session: {str(e)}")
        return None, None, None

def find_common_words(texts):
    """Find common words across all texts."""
    preprocessed_texts = [text.lower().split() for text in texts]
    all_words = [word for text in preprocessed_texts for word in text]
    word_counts = {word: all_words.count(word) for word in set(all_words)}
    return {word for word, count in word_counts.items() if count == len(texts)}

def calculate_similarity(text1, text2):
    """Calculate cosine similarity between two texts."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode([text1, text2])
    cosine_similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
    return cosine_similarity

def perform_lsa(texts, n_components=2):
    """Perform Latent Semantic Analysis on the given texts."""
    # Vectorize the texts
    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform(texts)

    # Apply LSA using TruncatedSVD
    lsa = TruncatedSVD(n_components=n_components)
    lsa_result = lsa.fit_transform(vectors)

    return lsa_result

def show_similar_words():
    st.title("Text Comparison and LSA Analysis")

    # Load texts from session state using the load_data_from_session function
    applicant_text, optimized_text, job_text = load_data_from_session()

    # Check if the texts are loaded successfully
    if not all([applicant_text, optimized_text, job_text]):
        st.error("Failed to load texts from session state.")
        return

    # Display loaded texts
    st.subheader("Loaded Texts")
    st.write("### Applicant Text")
    st.markdown(applicant_text)
    st.write("### Optimized Text")
    st.markdown(optimized_text)
    st.write("### Job Text")
    st.markdown(job_text)

    if st.button("Compare Texts"):
        # Find common words for each comparison pair
        common_words_applicant_job = find_common_words([applicant_text, job_text])
        common_words_optimized_job = find_common_words([optimized_text, job_text])
        common_words_applicant_optimized = find_common_words([applicant_text, optimized_text])

        # Display common words without highlighting
        st.write("### **Original vs Job Posting**")
        #st.write("**Original Text**")
        #st.markdown(applicant_text)  # Original Text
        #st.write("**Job Posting**")
        #st.markdown(job_text)  # Job Posting Text
        st.write("**Similar Words**")
        st.write(", ".join(common_words_applicant_job) if common_words_applicant_job else "No common words")

        st.write("---")

        st.write("### **Optimized vs Job Posting**")
        #st.write("**Optimized Text**")
        #st.markdown(optimized_text)  # Optimized Text
        #st.write("**Job Posting**")
        #st.markdown(job_text)  # Job Posting Text
        st.write("**Similar Words**")
        st.write(", ".join(common_words_optimized_job) if common_words_optimized_job else "No common words")

        st.write("---")

        st.write("### **Original vs Optimized**")
        #st.write("**Original Text**")
        #st.markdown(applicant_text)  # Original Text
        #st.write("**Optimized Text**")
        #st.markdown(optimized_text)  # Optimized Text
        st.write("**Similar Words**")
        st.write(", ".join(common_words_applicant_optimized) if common_words_applicant_optimized else "No common words")

        count_applicant_job = count_similar_words(applicant_text, job_text)
        count_optimized_job = count_similar_words(optimized_text, job_text)
        count_applicant_optimized = count_similar_words(applicant_text, optimized_text)

        # Display counts
        st.write("### Similar Words Count")
        st.write(f"**Original vs Job Posting:** {count_applicant_job} similar words")
        st.write(f"**Optimized vs Job Posting:** {count_optimized_job} similar words")
        st.write(f"**Original vs Optimized:** {count_applicant_optimized} similar words")

        # Save similarity scores in session state
        st.session_state.count_applicant_vs_job = count_applicant_job
        st.session_state.count_optimized_vs_job = count_optimized_job
        st.session_state.count_applicant_vs_optimized = count_applicant_optimized


        # Prepare the table data
        data = {
            "Comparison": ["Original vs Job Posting", "Optimized vs Job Posting", "Original vs Optimized"],
            "Similarity Score": [
                calculate_similarity(applicant_text, job_text),
                calculate_similarity(optimized_text, job_text),
                calculate_similarity(applicant_text, optimized_text)
            ],
            "Common Words": [
                ", ".join(common_words_applicant_job) if common_words_applicant_job else "No common words",
                ", ".join(common_words_optimized_job) if common_words_optimized_job else "No common words",
                ", ".join(common_words_applicant_optimized) if common_words_applicant_optimized else "No common words"
            ]
        }

        # Convert to DataFrame for table display
        df = pd.DataFrame(data)

        # Display the table with similarity scores and common words
        st.subheader("Comparison Results Table")
        st.dataframe(df)

        # Perform LSA
        texts = [applicant_text, optimized_text, job_text]
        lsa_result = perform_lsa(texts)

        # Display LSA results
        st.subheader("Latent Semantic Analysis Results")
        for i, text in enumerate(texts):
            st.write(f"**Text {i + 1}:** {text}")
            st.write(f"**LSA Representation:** {lsa_result[i]}")
            st.write("---")  # Separator for better readability

         # Display for applicant_text
        st.write("**Applicant Resume:**")
        #st.write(applicant_text)
        st.write("**LSA Representation:**")
        st.write(lsa_result[0])
        st.write("---")  # Separator for better readability

        # Display for optimized_text
        st.write("**Optimized Resume:**")
        #st.write(optimized_text)
        st.write("**LSA Representation:**")
        st.write(lsa_result[1])
        st.write("---")  # Separator for better readability

        # Display for job_text
        st.write("**Job Posting**")
        #st.write(job_text)
        st.write("**LSA Representation:**")
        st.write(lsa_result[2])
        st.write("---")  # Separator for better readability

        st.session_state.lsa_applicant = lsa_result[0]
        st.session_state.lsa_optimized = lsa_result[1]
        st.session_state.lsa_job = lsa_result[2]

        save_session_data_to_csv()

    if st.button("Create PDF"):
        st.session_state.page = "create resume"  # Change to the Create PDF page
            