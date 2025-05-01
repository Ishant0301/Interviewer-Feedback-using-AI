import os
from dotenv import load_dotenv
import json
import sqlite3
import requests
import assemblyai as aai
from moviepy.video.io.VideoFileClip import VideoFileClip
import streamlit as st
from PIL import Image
import numpy as np

# Load environment variables
load_dotenv()

# Configure APIs
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize the database
def initialize_database():
    if os.path.exists("candidate_database.db"):
        os.remove("candidate_database.db")

    conn = sqlite3.connect("candidate_database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        Name TEXT NOT NULL,
        Email TEXT PRIMARY KEY,
        InterviewDate TEXT,
        AppliedRole TEXT,
        VideoInterviewLink TEXT
    );
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO candidates (Name, Email, InterviewDate, AppliedRole, VideoInterviewLink)
        VALUES ('Shivang Rustagi', 'john.doe@example.com', '2023-10-15', 'Data Scientist', 'https://drive.google.com/file/d/1O8nLXUz_N8IMUIjgSfuDCkQ3su20CqUq/view?usp=sharing');
        """)
        cursor.execute("""
        INSERT INTO candidates (Name, Email, InterviewDate, AppliedRole, VideoInterviewLink)
        VALUES ('Jane Smith', 'jane.smith@example.com', '2023-10-16', 'Software Engineer', 'https://drive.google.com/file/d/1SJD0uZq-NTGBhTyF5veKfOD9E0hzN1Me/view?usp=sharing');
        """)
        conn.commit()

    conn.close()

def download_video(drive_url, video_path="downloaded_video.mp4"):
    file_id = drive_url.split('/d/')[1].split('/')[0]
    download_url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(video_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=108192):
                file.write(chunk)
        
        return video_path
    except requests.RequestException as e:
        st.error(f"Failed to download video: {e}")
        return None

def get_video_duration(video_path):
    """
    Get the duration of the video using moviepy.
    """
    try:
        video_clip = VideoFileClip(video_path)
        duration = video_clip.duration
        video_clip.close()
        return duration
    except Exception as e:
        st.error(f"Error getting video duration: {e}")
        return None

def transcribe_video(video_path):
    """
    Transcribe video directly using AssemblyAI's video-to-text API.
    """
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(video_path)
        return transcript
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return None

def get_first_frame(video_path, timestamp):
    """
    Get the first frame of a video segment as an image.
    """
    try:
        video_clip = VideoFileClip(video_path)
        frame = video_clip.get_frame(timestamp)
        video_clip.close()
        
        # Convert numpy array to PIL Image
        frame_image = Image.fromarray(frame)
        return frame_image
    except Exception as e:
        st.error(f"Error extracting first frame: {e}")
        return None


def analyze_transcription_and_generate_feedback(transcription, video_duration):
    """
    Analyze the transcription and generate feedback for all questions in a single API request.
    Group questions by category.
    """
    prompt = f"""
    Below is a transcription of an interview. Perform the following tasks:
    1. Extract the interviewer's questions and the candidate's answers.
    2. Categorize each question (e.g., EDA, AI, JavaScript, etc.).
    3. For each question-answer pair, generate feedback including:
       - A summary of the candidate's performance.
       - A score (0-100 scale) for the category.
       - A list of pros and cons for the candidate's answer.
    4. Include the start and end timestamps for each question-answer pair (relative to the start of the video).
    5. Group questions with the same category into a single block.

    Transcription:
    {transcription.text}

    Return the data in STRICT JSON format as follows:
    {{
        "categories": [
            {{
                "category": "Category/topic of the question",
                "questions_and_answers": [
                    {{
                        "question": "Interviewer's question",
                        "answer": "Candidate's answer",
                        "feedback": {{
                            "feedback_summary": "A short summary of the candidate's response",
                            "score": "Score based on knowledge demonstrated in the category",
                            "pros": ["List of strengths in the candidate's answer"],
                            "cons": ["List of weaknesses in the candidate's answer"]
                        }},
                        "start_time": "Start time of the question in seconds (relative to video start)",
                        "end_time": "End time of the answer in seconds (relative to video start)"
                    }},
                    ...
                ]
            }},
            ...
        ]
    }}

    IMPORTANT:
    - Return ONLY valid JSON. Do not include any additional text or explanations.
    - Ensure all timestamps are relative to the start of the video.
    - Ensure the JSON is properly formatted and can be parsed by a JSON parser.
    """
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen/qwen2.5-vl-32b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Extract the content from the response
        response_text = response_data['choices'][0]['message']['content'].strip()
        
        # Clean the response text
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()

        # Parse the JSON response
        data = json.loads(response_text)
        return data["categories"]
    except json.JSONDecodeError:
        st.error("The API response is not valid JSON. Please check the prompt or API output.")
        st.write("Raw API Response:", response_text)
        return None
    except Exception as e:
        st.error(f"An error occurred while analyzing the transcription: {e}")
        return None