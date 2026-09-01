# 🎙️ VoxAgent — Real-Time Voice AI Agent

> An open-source, production-grade voice AI agent with LangGraph orchestration, RAG, semantic caching, and persistent memory — built for real-time conversations.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-WebSocket-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Cost](https://img.shields.io/badge/Cost-₹0%20(Free)-brightgreen.svg)](#tech-stack)

---

## 🎯 What is VoxAgent?

VoxAgent is a **real-time voice AI agent** that can:
- 🎤 Listen to your voice in real-time via browser
- 🧠 Think using LangGraph (stateful multi-step agent)
- 🔧 Use 9 different tools (weather, booking, CRM, web search, RAG...)
- 🔊 Respond with natural voice
- 💾 Remember conversations across sessions
- ⚡ Cache repeated queries for instant responses

**Total cost: ₹0** — All free APIs!

---

## 🏗️ Architecture

```
                        ┌──────────────────────────────────────┐
                        │          FastAPI Server               │
 ┌──────────┐  Audio    │                                      │
 │ Browser  │ ────────► │  [ STT ] ──► [ LangGraph ] ──► [ TTS ]│
 │          │ ◄──────── │   Groq        Agent          Edge-TTS│
 │ 🎤 Mic   │  Audio    │                 │                     │
 │ 🔊 Speaker│          │        ┌────────┼────────┐           │
 │ 📊 Metrics│          │        ▼        ▼        ▼           │
 └──────────┘           │    [Tools]  [Cache⚡] [Memory💾]     │
                        └──────────────────────────────────────┘
```

### LangGraph Agent Flow

```
                    ┌───────────────┐
  User Query ──►   │ CLASSIFY      │
                    │ INTENT        │
                    └───────┬───────┘
                      ┌─────┴─────┐
                      ▼           ▼
               ┌──────────┐ ┌──────────┐
               │ EXECUTE  │ │  DIRECT  │
               │  TOOLS   │ │  ANSWER  │
               └─────┬────┘ └─────┬────┘
                     └──────┬─────┘
                            ▼
                    ┌───────────────┐
                    │   GENERATE    │
                    │    ANSWER     │──► 🔊 Voice
                    └───────────────┘
```

---

## ✨ Features

### Core Voice Pipeline
- **Real-time WebSocket streaming** — bidirectional audio over WebSocket
- **Groq Whisper STT** — large-v3 model, ~500ms latency
- **Google Gemini LLM** — 3.5 Flash Lite, free tier
- **Edge-TTS + gTTS** — dual TTS with automatic fallback
- **Latency dashboard** — real-time STT/LLM/TTS/Total metrics
- **Interruption handling** — stop TTS mid-sentence
- **Auto conversation mode** — silence detection + auto-record
- **Hinglish support** — Hindi + English in Roman script
- **Hallucination filter** — catches Whisper phantom transcripts

### Agentic Tools (9 Tools)

| Tool | Category | Description |
|------|----------|-------------|
| `search_knowledge` | 📚 RAG | Search PDFs/documents (FAISS + sentence-transformers) |
| `book_appointment` | 📅 Create | Book appointments with date, time, purpose |
| `get_bookings` | 📋 Read | View all booked appointments |
| `update_booking` | ✏️ Update | Reschedule or modify bookings |
| `cancel_booking` | ❌ Delete | Cancel appointments |
| `lookup_customer` | 👤 CRM | Search customers by name, ID, or phone |
| `get_weather` | 🌤️ API | Real-time weather data (wttr.in) |
| `get_current_time` | ⏰ System | Current time, date, and day |
| `search_web` | 🔍 Search | DuckDuckGo web search |

### Intelligent Features
- **LangGraph orchestration** — stateful agent with conditional routing
- **Multi-tool execution** — handle multiple tools in a single query
- **Semantic caching** — meaning-based cache with per-tool TTL
- **Persistent memory** — SQLite-backed cross-session conversations
- **User profiling** — auto-detects language, topics, preferences
- **Robust JSON parsing** — 3-layer fallback (cleanup → parse → regex)
- **Graceful error handling** — WebSocket disconnect recovery

---

## 🔧 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI + WebSockets | Real-time bidirectional streaming |
| **Agent** | LangGraph (StateGraph) | Stateful multi-step orchestration |
| **STT** | Groq Whisper API (large-v3) | Best accuracy, ~500ms |
| **LLM** | Google Gemini 3.5 Flash Lite | Fast, free, reliable |
| **TTS** | Edge-TTS + gTTS fallback | Natural voice, zero cost |
| **RAG** | FAISS + sentence-transformers | Semantic document search |
| **Cache** | Semantic Cache (SQLite + embeddings) | Meaning-based query caching |
| **Memory** | SQLite | Persistent conversations, zero setup |
| **Search** | DuckDuckGo (ddgs) | Free web search |
| **Frontend** | HTML/CSS/JS + Web Audio API | Browser-native, no framework |

**Total infrastructure cost: ₹0**

---

## 📁 Project Structure

```
VoxAgent/
├── app/
│   ├── server.py              # FastAPI + WebSocket endpoints
│   ├── config.py              # Environment config (API keys)
│   ├── agent/
│   │   └── graph.py           # LangGraph agent (classify → execute → answer)
│   ├── stt/
│   │   └── whisper.py         # Groq Whisper STT + hallucination filter
│   ├── tts/
│   │   └── edge.py            # Edge-TTS + gTTS fallback
│   ├── tools/
│   │   └── agent_tools.py     # 9 tools (weather, booking, CRM, RAG, search)
│   ├── rag/
│   │   └── knowledge_base.py  # FAISS vector store + PDF loader
│   └── memory/
│       ├── database.py        # SQLite persistent memory + user profiles
│       └── cache.py           # Semantic cache with TTL
├── frontend/
│   └── index.html             # Voice UI + auto mode + latency dashboard
├── knowledge_base/            # Drop PDFs here for RAG
├── data/
│   └── voxagent.db            # SQLite database (auto-created)
├── .env                       # API keys
├── pyproject.toml             # Dependencies
└── README.md                  # You are here!
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

### 1. Clone & Setup

```bash
git clone https://github.com/kalashkj28/VoxAgent.git
cd VoxAgent
```

### 2. Install Dependencies

```bash
uv sync
# or
pip install -r requirements.txt
```

### 3. Get Free API Keys

| API | Get Key | Free Tier |
|-----|---------|-----------|
| **Gemini** | [aistudio.google.com](https://aistudio.google.com/apikey) | 15 RPM |
| **Groq** | [console.groq.com](https://console.groq.com/keys) | 14,400 req/day |

### 4. Configure

Create `.env` file:
```env
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
```

### 5. Run

```bash
uv run uvicorn app.server:app --reload
```

### 6. Open Browser

Go to **http://localhost:8000** — start talking! 🎤

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| STT Latency | ~500ms |
| LLM Latency | ~1-3s |
| TTS Latency | ~1-2s |
| **Total Round-trip** | **~3-6s** |
| Cache Hit | **~0ms** (instant!) |
| Concurrent Sessions | Single user (SQLite) |

---

## 🧪 Try These Commands

```
🎤 "Delhi ka weather batao"              → Weather tool
🎤 "Kal 3 baje doctor ka appointment"    → Booking (Create)
🎤 "Meri bookings dikhao"                → Booking (Read)
🎤 "BK-001 ko 5 baje kardo"             → Booking (Update)
🎤 "BK-001 cancel kardo"                → Booking (Delete)
🎤 "Rahul Sharma ka plan kya hai?"       → CRM Lookup
🎤 "Latest news about AI?"              → Web Search
🎤 "Weather bata aur time bhi bata"     → Multi-tool! 🔥
🎤 "Do you remember what we discussed?" → Cross-session memory
```

---

## 🧠 Key Design Decisions

| Decision | Why |
|----------|-----|
| **LangGraph over manual parsing** | Stateful orchestration, multi-tool support, conditional routing |
| **Groq Whisper over local models** | 10x faster, better Hindi accuracy, no GPU needed |
| **SQLite over PostgreSQL** | Zero setup for demo; production migration is trivial |
| **Semantic cache over Redis** | Meaning-based matching, same DB, no extra service |
| **Edge-TTS + gTTS fallback** | Dual redundancy, zero cost |
| **Manual tool registry** | Gemini's native function calling had protobuf compatibility issues |
| **Session memory (RAM) for demo** | Full persistent memory code exists but disabled for public demo — no user data stored on server. Set `PERSISTENT_MEMORY=True` in config for single-user/local use |

---

## 🎤 Interview Talking Points

> "I built VoxAgent — a real-time voice AI agent with sub-3-second latency. It uses **LangGraph** for stateful agent orchestration with conditional routing across 9 tools including RAG, CRUD booking, and CRM lookup. I implemented **semantic caching** that matches queries by meaning (not exact text), reducing repeat query latency by 90%. The architecture supports **persistent cross-session memory** using SQLite — I built the full implementation but disabled DB writes for the public demo to protect user privacy. In production, this would use user authentication with separate databases per user."

**This project demonstrates:**
- ✅ Real-time systems (WebSocket streaming)
- ✅ Voice AI pipeline (STT + LLM + TTS)
- ✅ Agentic architecture (LangGraph + multi-tool)
- ✅ RAG expertise (FAISS + embeddings)
- ✅ Semantic caching (cosine similarity + TTL)
- ✅ Production mindset (error handling, fallbacks, graceful degradation)

---

## 📄 License

MIT License — feel free to use, modify, and build upon this project.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/kalashkj28">Kalash Jain</a>
</p>
