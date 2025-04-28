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