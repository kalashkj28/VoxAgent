"""Configuration settings for VoxAgent."""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

TTS_VOICE = "en-IN-NeerjaNeural"
PERSISTENT_MEMORY = False
HOST = "0.0.0.0"
PORT = 8000

def validate_config():
    """Validate required configuration settings."""
    valid = True
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
        print("⚠️ WARNING: GEMINI_API_KEY not set in .env file!")
        print("   Get your key from: https://aistudio.google.com/apikey")
        valid = False
    if not GROQ_API_KEY or GROQ_API_KEY == "your_api_key_here":
        print("⚠️ WARNING: GROQ_API_KEY not set in .env file!")
        print("   Get your key from: https://console.groq.com/keys")
        valid = False
    if valid:
        print("✅ Config loaded successfully")
    return valid
