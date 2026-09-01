"""Main Server for Voice AI Agent."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import google.generativeai as genai
import json
import time
import os
import glob

from app.stt.whisper import SpeechToText
from app.tts.edge import TextToSpeech
from app.config import GEMINI_API_KEY, GROQ_API_KEY, TTS_VOICE, validate_config
from app.rag.knowledge_base import kb
from app.agent.graph import run_agent
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI(title="VoxAgent", description="Real-time Voice AI Agent")

validate_config()
genai.configure(api_key=GEMINI_API_KEY)

stt = SpeechToText(api_key=GROQ_API_KEY)
tts = TextToSpeech(voice=TTS_VOICE)

for f in glob.glob(os.path.join("knowledge_base", "*.pdf")):
    os.remove(f)
print("📚 KB ready (empty — upload PDFs from UI)")

is_tts_enabled = True

async def get_llm_response(user_text: str) -> dict:
    """Pass user query to LangGraph agent and return response."""
    return await run_agent(user_text)

@app.get("/")
async def home():
    """Serve frontend HTML page."""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    return FileResponse(frontend_path)

@app.post("/api/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    """Upload PDF and reload KB."""
    if not file.filename.endswith(".pdf"):
        return JSONResponse({"error": "Only PDF files allowed!"}, status_code=400)
    
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)
    
    file_path = os.path.join(kb_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    kb.load_documents()
    
    print(f"📚 Uploaded: {file.filename} | KB ready: {kb.is_ready} | Chunks: {len(kb.chunks)}")
    
    return {
        "message": f"'{file.filename}' uploaded successfully!",
        "total_chunks": len(kb.chunks),
        "is_ready": kb.is_ready
    }

@app.get("/api/knowledge/status")
async def knowledge_status():
    """Get current KB status."""
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    files = [f for f in os.listdir(kb_dir) if f.endswith(".pdf")] if os.path.exists(kb_dir) else []
    
    return {
        "is_ready": kb.is_ready,
        "total_chunks": len(kb.chunks),
        "files": files
    }

@app.delete("/api/knowledge/clear")
async def clear_knowledge():
    """Delete all PDFs to clear KB."""
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    if os.path.exists(kb_dir):
        for f in os.listdir(kb_dir):
            if f.endswith(".pdf"):
                os.remove(os.path.join(kb_dir, f))
    
    kb.chunks = []
    kb.index = None
    kb.is_ready = False
    print("🧹 KB cleared — fresh session!")
    return {"message": "Knowledge base cleared!", "total_chunks": 0}

@app.delete("/api/knowledge/{filename}")
async def delete_knowledge(filename: str):
    """Delete a PDF and reload KB."""
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    file_path = os.path.join(kb_dir, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        kb.load_documents()
        print(f"🗑️ Deleted: {filename} | KB chunks: {len(kb.chunks)}")
        return {"message": f"'{filename}' deleted!", "total_chunks": len(kb.chunks)}
    
    return JSONResponse({"error": "File not found!"}, status_code=404)

@app.websocket("/ws/voice")
async def voice_pipeline(websocket: WebSocket):
    """Main voice pipeline endpoint: STT -> LLM -> TTS."""
    await websocket.accept()
    print("\n✅ Voice client connected!")
    
    try:
        is_auto_mode = False
        global is_tts_enabled
        
        while True:
            message = await websocket.receive()
            
            if "text" in message:
                data = message["text"]
                if "cancel" in data:
                    print("🛑 Cancel signal received")
                elif "auto_on" in data:
                    is_auto_mode = True
                    print("🔁 Auto mode: ON")
                elif "auto_off" in data:
                    is_auto_mode = False
                    print("🔁 Auto mode: OFF")
                elif "tts_off" in data:
                    is_tts_enabled = False
                    print("🔇 TTS: OFF")
                elif "tts_on" in data:
                    is_tts_enabled = True
                    print("🔊 TTS: ON")
                continue
            
            audio_bytes = message.get("bytes", b"")
            total_start = time.time()
            print(f"\n📩 Received audio: {len(audio_bytes)} bytes")
            
            if len(audio_bytes) < 1000:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Audio too short! Speak longer (2-3 seconds)."
                }))
                continue
            
            try:
                stt_result = await stt.transcribe(audio_bytes)
                user_text = stt_result["text"]
                
                if not user_text.strip():
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Nothing heard, please repeat!"
                    }))
                    continue
                
                await websocket.send_text(json.dumps({
                    "type": "transcript",
                    "text": user_text,
                    "language": stt_result["language"],
                    "stt_ms": stt_result["duration_ms"]
                }))
                
                llm_result = await get_llm_response(user_text)
                
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "text": llm_result["text"],
                    "llm_ms": llm_result["duration_ms"]
                }))
                
                if is_tts_enabled:
                    tts_result = await tts.synthesize(llm_result["text"])
                    tts_ms = tts_result["duration_ms"]
                else:
                    tts_ms = 0
                
                total_ms = (time.time() - total_start) * 1000
                
                await websocket.send_text(json.dumps({
                    "type": "metrics",
                    "stt_ms": stt_result["duration_ms"],
                    "llm_ms": llm_result["duration_ms"],
                    "tts_ms": tts_ms,
                    "total_ms": round(total_ms)
                }))
                
                if is_tts_enabled:
                    await websocket.send_bytes(tts_result["audio"])
                
                print(f"✅ Total pipeline: {total_ms:.0f}ms")
            
            except (WebSocketDisconnect, RuntimeError) as e:
                print(f"⚠️ Client disconnected during pipeline: {e}")
                return
            except Exception as e:
                print(f"❌ Pipeline error: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Error: {str(e)[:100]}. Try again!"
                    }))
                except Exception:
                    print("⚠️ Could not send error")
                    return
            
    except WebSocketDisconnect:
        print("❌ Voice client disconnected!")

@app.websocket("/ws/chat")
async def text_chat(websocket: WebSocket):
    """Text chat endpoint."""
    await websocket.accept()
    print("✅ Text chat client connected!")
    
    try:
        while True:
            message = await websocket.receive_text()
            
            if message in ("tts_on", "tts_off"):
                global is_tts_enabled
                is_tts_enabled = message == "tts_on"
                print(f"{'🔊' if is_tts_enabled else '🔇'} TTS: {'ON' if is_tts_enabled else 'OFF'}")
                continue
            
            print(f"📩 Text: {message}")
            
            try:
                llm_result = await get_llm_response(message)
                
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "text": llm_result["text"],
                    "llm_ms": llm_result["duration_ms"]
                }))
                
                if is_tts_enabled:
                    tts_result = await tts.synthesize(llm_result["text"])
                    tts_ms = tts_result["duration_ms"]
                else:
                    tts_ms = 0
                
                await websocket.send_text(json.dumps({
                    "type": "metrics",
                    "stt_ms": 0,
                    "llm_ms": llm_result["duration_ms"],
                    "tts_ms": tts_ms,
                    "total_ms": llm_result["duration_ms"] + tts_ms
                }))
                
                if is_tts_enabled:
                    await websocket.send_bytes(tts_result["audio"])
                
            except (WebSocketDisconnect, RuntimeError) as e:
                print(f"⚠️ Chat client disconnected: {e}")
                return
            except Exception as e:
                print(f"❌ Chat error: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Error: {str(e)[:100]}"
                    }))
                except Exception:
                    print("⚠️ Could not send error")
                    return
            
    except WebSocketDisconnect:
        print("❌ Text chat client disconnected!")
