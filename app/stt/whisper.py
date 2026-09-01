"""Speech-to-Text using Groq Whisper API."""

import time
import httpx

HALLUCINATIONS = [
    "thank you for watching",
    "thanks for watching", 
    "please subscribe",
    "please like and subscribe",
    "like and subscribe",
    "see you in the next video",
    "see you next time",
    "bye bye",
    "goodbye",
    "thank you",
    "you",
    "the end",
    "so",
    "okay",
    "hmm",
    "um",
    "uh",
    "walaikum salam",
    "assalamu alaikum",
    "salam alaikum",
    "just play",
]

class SpeechToText:
    """Audio to Text converter using Groq Whisper API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        print("✅ Groq Whisper STT initialized (large-v3 model)")
    
    async def transcribe(self, audio_bytes: bytes) -> dict:
        """Convert audio bytes to text."""
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    files={
                        "file": ("audio.webm", audio_bytes, "audio/webm")
                    },
                    data={
                        "model": "whisper-large-v3",
                        "response_format": "json",
                        "language": "en",
                        "prompt": "Haan bhai, kya haal hai? Aaj ka din kaisa chal raha hai? Bhai tu chup hoja, mujhe kuch batana hai. Acha sun, mujhe ek kaam karna hai. What's the weather in Delhi today? Yaar mujhe ek joke sunao na. Mera naam kya hai?",
                    }
                )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error {response.status_code}: {response.text}")
            
            result = response.json()
            text = result.get("text", "").strip()
            
            text_lower = text.lower().strip().rstrip(".!?,")
            if text_lower in HALLUCINATIONS or len(text_lower) < 3:
                print(f"🛡️ Hallucination filtered: '{text}'")
                text = ""
            
            duration_ms = (time.time() - start) * 1000
            
            print(f"🎤 STT: '{text}' | Time: {duration_ms:.0f}ms")
            
            return {
                "text": text,
                "language": "auto",
                "duration_ms": round(duration_ms)
            }
            
        except Exception as e:
            print(f"❌ STT Error: {e}")
            return {
                "text": "",
                "language": "unknown",
                "duration_ms": 0
            }
