import pandas as pd
import openai
import os
from tqdm import tqdm
import time
import chardet

# Set DeepSeek API configuration
openai.api_key = "sk-1a27d4ea17a2449f96897f8cc0e02875"
openai.base_url = "https://api.deepseek.com"

# List of available majors
majors = [
    "BACHELOR OF ARTS IN MASS COMMUNICATION",
    "BACHELOR OF SCIENCE IN BIOTECHNOLOGY",
    "BACHELOR OF SCIENCE IN BUSINESS ADMINISTRATION",
    "BACHELOR OF ARCHITECTURE",
    "BACHELOR OF ARTS IN INTERIOR DESIGN",
    "BACHELOR OF SCIENCE IN ARTIFICIAL INTELLIGENCE",
    "BACHELOR OF SCIENCE IN CHEMICAL ENGINEERING",
    "BACHELOR OF SCIENCE IN CIVIL AND INFRASTRUCTURE ENGINEERING",
    "BACHELOR OF SCIENCE IN COMPUTER ENGINEERING",
    "BACHELOR OF SCIENCE IN COMPUTER SCIENCE",
    "BACHELOR OF SCIENCE IN ELECTRICAL AND ELECTRONICS ENGINEERING",
    "BACHELOR OF SCIENCE IN MECHANICAL ENGINEERING",
    "BACHELOR OF SCIENCE IN PETROLEUM ENGINEERING"
]

def detect_encoding(file_path):
    """
    Detect the encoding of a file
    """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def recommend_major(student_data):
    """
    Use the DeepSeek API to recommend a major based on student data
    """
    # Select only relevant columns for determining major
    # Customize this list based on your actual column names
    relevant_fields = [
        "interests", "skills", "subjects", "scores", "aptitude", 
        "academic_performance", "favorite_subjects", "career_goals",
        "math_score", "science_score", "english_score", "history_score",
        "gpa", "extracurricular"
        # Add any other relevant fields from your dataset
    ]
    
    # Filter to only include fields that exist in the data
    filtered_data = {k: v for k, v in student_data.items() 
                    if k in relevant_fields and pd.notna(v)}
    
    # Format the filtered student data for the prompt
    student_info = "\n".join([f"{key}: {value}" for key, value in filtered_data.items()])
    
    # If we don't have any relevant data, use all non-null data as a fallback
    if not student_info:
        filtered_data = {k: v for k, v in student_data.items() 
                         if pd.notna(v) and k != 'best_fit'}
        student_info = "\n".join([f"{key}: {value}" for key, value in filtered_data.items()])
    
    # Create a prompt for the API
    prompt = f"""
    Based on the following student information, recommend the most suitable major from the list provided.
    
    Student Information:
    {student_info}
    
    Available Majors:
    {', '.join(majors)}
    
    Recommend only one major from the list that would be the best fit for this student based on their information.
    Only return the name of the major, no explanation needed.
    """
    
    try:
        # Make the API call to DeepSeek
        response = openai.chat.completions.create(
            model="deepseek-chat",  # Using DeepSeek's model
            messages=[
                {"role": "system", "content": "You are an academic advisor helping to match students with appropriate majors."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.2  # Low temperature for more consistent results
        )
        
        # Extract and return the recommended major
        recommendation = response.choices[0].message.content.strip()
        
        # Validate that the recommendation is in our list of majors
        for major in majors:
            if major in recommendation:
                return major
        
        # If no exact match, return the recommendation anyway
        return recommendation
    
    except Exception as e:
        print(f"Error with DeepSeek API call: {e}")
        return "ERROR: Could not determine recommendation"

def process_student_data(file_path):
    """
    Process student data from the file, get recommendations, 
    and add them to a 'best_fit' column in the same file
    """
    try:
        # Detect the file encoding
        encoding = detect_encoding(file_path)
        print(f"Detected file encoding: {encoding}")
        
        # Read the data file with the detected encoding
        df = pd.read_csv(file_path, encoding=encoding)
        
        # Create a backup of the original file
        backup_path = file_path.replace(".csv", "_backup.csv")
        df.to_csv(backup_path, index=False, encoding=encoding)
        print(f"Original file backed up to: {backup_path}")
        
        # Create or overwrite the 'best_fit' column
        df['best_fit'] = None
        
        # Process each row
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing students"):
            # Convert row to dictionary for easier handling
            student_data = row.to_dict()
            
            # Get recommendation
            recommendation = recommend_major(student_data)
            
            # Save recommendation to dataframe
            df.at[index, 'best_fit'] = recommendation
            
            # Sleep briefly to avoid hitting API rate limits
            time.sleep(0.5)
            
            # Periodically save progress (e.g., every 10 rows)
            if index % 10 == 0 and index > 0:
                df.to_csv(file_path, index=False, encoding=encoding)
                print(f"Progress saved at row {index}")
        
        # Save the final results back to the same file
        df.to_csv(file_path, index=False, encoding=encoding)
        print(f"Recommendations complete. Results saved to original file: {file_path}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        print("Try specifying the encoding manually, e.g., 'latin1', 'cp1252', or 'ISO-8859-1'")

# Example usage
if __name__ == "__main__":
    file_path = "Exploring Your Future_ Major Selection Survey(Sheet1).csv"  # Replace with your input file path
    
    # If automatic detection fails, you can specify encoding manually like this:
    # process_student_data_with_encoding(file_path, "latin1")  # or "cp1252", "ISO-8859-1", etc.
    
    process_student_data(file_path)

# If automatic detection fails, you can use this function instead
def process_student_data_with_encoding(file_path, encoding):
    """
    Process student data with a manually specified encoding
    """
    try:
        # Read the data file with the specified encoding
        df = pd.read_csv(file_path, encoding=encoding)
        print(f"Successfully read file with encoding: {encoding}")
        
        # Create a backup of the original file
        backup_path = file_path.replace(".csv", "_backup.csv")
        df.to_csv(backup_path, index=False, encoding=encoding)
        print(f"Original file backed up to: {backup_path}")
        
        # Create or overwrite the 'best_fit' column
        df['best_fit'] = None
        
        # Process each row
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing students"):
            # Convert row to dictionary for easier handling
            student_data = row.to_dict()
            
            # Get recommendation
            recommendation = recommend_major(student_data)
            
            # Save recommendation to dataframe
            df.at[index, 'best_fit'] = recommendation
            
            # Sleep briefly to avoid hitting API rate limits
            time.sleep(0.5)
            
            # Periodically save progress
            if index % 10 == 0 and index > 0:
                df.to_csv(file_path, index=False, encoding=encoding)
                print(f"Progress saved at row {index}")
        
        # Save the results back to the same file
        df.to_csv(file_path, index=False, encoding=encoding)
        print(f"Recommendations complete. Results saved to original file: {file_path}")
        
    except Exception as e:
        print(f"Error processing file with encoding {encoding}: {e}")