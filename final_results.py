import pandas as pd
import streamlit as st
import os

def save_session_data_to_csv():
    """Load session data and save it to a CSV file, appending new data."""
    try:
        # Prepare the data to be saved
        data = {
            "Cosine Applicant vs Job": [st.session_state.get("cosine_applicant_vs_job", 0)],
            "Cosine Optimized vs Job": [st.session_state.get("cosine_optimized_vs_job", 0)],
            "Cosine Applicant vs Optimized": [st.session_state.get("cosine_applicant_vs_optimized", 0)],
            "Jaccard Applicant vs Job": [st.session_state.get("jaccard_applicant_vs_job", 0)],
            "Jaccard Optimized vs Job": [st.session_state.get("jaccard_optimized_vs_job", 0)],
            "Jaccard Applicant vs Optimized": [st.session_state.get("jaccard_applicant_vs_optimized", 0)],
            "SBERT Applicant vs Job": [st.session_state.get("sbert_applicant_vs_job", 0)],
            "SBERT Optimized vs Job": [st.session_state.get("sbert_optimized_vs_job", 0)],
            "SBERT Applicant vs Optimized": [st.session_state.get("sbert_applicant_vs_optimized", 0)],
            "Count Applicant vs Job": [st.session_state.get("count_applicant_vs_job", 0)],
            "Count Optimized vs Job": [st.session_state.get("count_optimized_vs_job", 0)],
            "Count Applicant vs Optimized": [st.session_state.get("count_applicant_vs_optimized", 0)],
            "LSA Applicant": [st.session_state.get("lsa_applicant", 0)],
            "LSA Optimized": [st.session_state.get("lsa_optimized", 0)],
            "LSA Job": [st.session_state.get("lsa_job", 0)],
        }

        # Create a DataFrame from the session data
        new_data_df = pd.DataFrame(data)

        # Define the CSV file path
        csv_file_path = "session_data.csv"

        # Check if the CSV file already exists
        if os.path.exists(csv_file_path):
            # Load existing data
            existing_data_df = pd.read_csv(csv_file_path)
            # Append new data
            updated_data_df = pd.concat([existing_data_df, new_data_df], ignore_index=True)
        else:
            # If the file does not exist, use the new data as the DataFrame
            updated_data_df = new_data_df

        # Save the updated DataFrame to the CSV file
        updated_data_df.to_csv(csv_file_path, index=False)

        st.success(f"Session data saved to {csv_file_path}")

    except Exception as e:
        st.error(f"Error saving session data to CSV: {str(e)}")


