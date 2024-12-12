import pandas as pd

def load_clean_and_show_statistics():
    """Load similarity data from similarity.csv, clean it, and show statistics for specific columns."""
    # Load the similarity data
    file_path = "similarity.csv"
    
    try:
        df = pd.read_csv(file_path)
        print("### Similarity Data Loaded Successfully ###")
        
        # Show the first few rows of the DataFrame before cleaning
        print("\n### Head of the Similarity Data Before Cleaning ###")
        print(df.head())  # Display the first 5 rows

        # Remove any empty rows
        df.dropna(how='all', inplace=True)  # Drop rows where all elements are NaN
        df.dropna(how='any', inplace=True)  # Drop rows where any element is NaN

        # Optionally, you can reset the index after dropping rows
        df.reset_index(drop=True, inplace=True)

        # Show the first few rows of the DataFrame after cleaning
        print("\n### Head of the Similarity Data After Cleaning ###")
        print(df.head())  # Display the first 5 rows after cleaning

        # Show statistics for columns 3, 4, and 5 (assuming 0-based indexing)
        print("\n### Statistics for Columns 3, 4, and 5 ###")
        print(df.iloc[:, 2:5].describe())  # Display statistics for columns 3, 4, and 5

    except FileNotFoundError:
        print("Error: similarity.csv file not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Call the function to load, clean, and show statistics
load_clean_and_show_statistics()