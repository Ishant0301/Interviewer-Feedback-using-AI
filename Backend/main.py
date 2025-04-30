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