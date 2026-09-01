"""Text-to-Speech using Edge-TTS with gTTS fallback."""

import time
import asyncio
import io
import edge_tts

VOICES = {
    "hindi_female": "hi-IN-SwaraNeural",
    "hindi_male": "hi-IN-MadhurNeural",
    "english_female": "en-IN-NeerjaNeural",
    "english_male": "en-IN-PrabhatNeural",
}

DEFAULT_VOICE = VOICES["hindi_female"]

class TextToSpeech:
    """TTS with Edge-TTS primary and gTTS fallback."""
    
    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice
        print(f"✅ TTS initialized with voice: {voice}")
    
    async def synthesize(self, text: str) -> dict:
        """Convert text to audio."""
        start = time.time()
        
        # Try Edge-TTS first (fast when available)
        try:
            audio_bytes = await self._edge_tts(text)
            duration_ms = (time.time() - start) * 1000
            print(f"🔊 TTS (Edge): '{text[:50]}...' | {len(audio_bytes)} bytes | {duration_ms:.0f}ms")
            return {"audio": audio_bytes, "duration_ms": round(duration_ms)}
        except Exception as e:
            print(f"⚠️ Edge-TTS failed: {e}, using gTTS")
        
        # Fallback to gTTS (always works)
        try:
            audio_bytes = await self._google_tts(text)
            duration_ms = (time.time() - start) * 1000
            print(f"🔊 TTS (gTTS): '{text[:50]}...' | {len(audio_bytes)} bytes | {duration_ms:.0f}ms")
            return {"audio": audio_bytes, "duration_ms": round(duration_ms)}
        except Exception as e:
            raise Exception(f"All TTS engines failed: {e}")
    
    async def _edge_tts(self, text: str) -> bytes:
        """Generate audio using Edge-TTS."""
        communicate = edge_tts.Communicate(text, self.voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        audio_bytes = b"".join(audio_chunks)
        if len(audio_bytes) == 0:
            raise Exception("Empty audio from Edge-TTS")
        return audio_bytes
    
    async def _google_tts(self, text: str) -> bytes:
        """Generate audio using gTTS."""
        def _generate():
            from gtts import gTTS
            lang = "hi"
            english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
            total_chars = sum(1 for c in text if c.isalpha())
            if total_chars > 0 and english_chars / total_chars > 0.7:
                lang = "en"
            tts = gTTS(text=text, lang=lang)
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            return mp3_buffer.getvalue()
        return await asyncio.to_thread(_generate)
    
    def set_voice(self, voice_key: str):
        """Change TTS voice."""
        if voice_key in VOICES:
            self.voice = VOICES[voice_key]
            print(f"🔄 Voice changed to: {self.voice}")
