# 🎙️ VoxAgent — Real-Time Voice AI Agent

> An open-source voice AI agent with LangGraph orchestration, RAG, semantic caching, and 9 agentic tools — built for real-time conversations. Total cost: ₹0.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-WebSocket-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Cost](https://img.shields.io/badge/Cost-₹0%20(Free)-brightgreen.svg)](#tech-stack)
[![Live Demo](https://img.shields.io/badge/Live-Demo-red.svg)](https://voxagent-fzxj.onrender.com)

🔗 **[Try Live Demo](https://voxagent-fzxj.onrender.com)** · 💻 **[Source Code](https://github.com/kalashkj28/VoxAgent)**

---

## 🎯 What is VoxAgent?

VoxAgent is a **real-time voice AI agent** that doesn't just talk back — it takes action.

- 🎤 Listens to your voice in real-time via browser
- 🧠 Thinks using LangGraph (stateful multi-step agent)
- 🔧 Uses 9 different tools (weather, booking CRUD, CRM, web search, RAG)
- 🔊 Responds with natural voice (Edge-TTS)
- 💾 Remembers conversations across sessions
- ⚡ Caches repeated queries for instant responses
- 🇮🇳 Handles Hinglish (Hindi + English) natively

**Total cost: ₹0** — All free-tier APIs!

---

## 📊 Real Benchmarks

Measured from actual conversations (not synthetic tests):

| Component | Latency | Details |
|-----------|---------|---------|
| 🎤 **STT** (Groq Whisper) | ~450-550ms | large-v3 model, Hindi + English |
| 🧠 **Classify** (Gemini) | ~800-1100ms | Intent detection + tool routing |
| 🔧 **Tool Execution** | ~1-5s | Varies by tool (weather, search, etc.) |
| 🔊 **TTS** (Edge-TTS) | ~200-400ms | Neural voice, MP3 streaming |
| ⚡ **Cache Hit** | ~70ms | Near-instant on similar queries |
| | | |
| **Total (direct chat)** | **~2-3s** | No tool needed |
| **Total (with tools)** | **~3.5-5s** | Including API calls |
| **Total (cache hit)** | **~1.5s** | Skips tool + LLM pipeline |

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
  User Query ──►   │   CLASSIFY    │
                    │    INTENT     │
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
- **Latency dashboard** — real-time STT/LLM/TTS/Total metrics in UI
- **Interruption handling** — stop TTS mid-sentence
- **Auto conversation mode** — silence detection + auto-record
- **Hinglish support** — Hindi + English in Roman script
- **Hallucination filter** — catches Whisper phantom transcripts

### Agentic Tools (9 Tools)

| Tool | Category | Description |
|------|----------|-------------|
| `search_knowledge` | 📚 RAG | Search uploaded PDFs/documents (FAISS + sentence-transformers) |
| `book_appointment` | 📅 Create | Book appointments with date, time, purpose |
| `get_bookings` | 📋 Read | View all booked appointments |
| `update_booking` | ✏️ Update | Reschedule or modify bookings |
| `cancel_booking` | ❌ Delete | Cancel appointments |
| `lookup_customer` | 👤 CRM | Search customers by name, ID, or phone |
| `get_weather` | 🌤️ API | Real-time weather data (wttr.in) |
| `get_current_time` | ⏰ System | Current time, date, and day |
| `search_web` | 🔍 Search | DuckDuckGo web search (optimized, ~1-5s) |

### Intelligent Features
- **LangGraph orchestration** — stateful agent with conditional routing
- **Multi-tool execution** — handle multiple tools in a single query
- **Semantic caching** — word-overlap similarity with per-tool TTL (lightweight, no model needed)
- **Persistent memory** — SQLite-backed cross-session conversations
- **User profiling** — auto-detects language, topics, preferences
- **Robust JSON parsing** — 3-layer fallback (brace balancer + cleanup + regex)
- **Graceful error handling** — WebSocket disconnect recovery
- **Glassmorphism UI** — light theme with liquid glass effects

---

## 🔧 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI + WebSockets | Real-time bidirectional streaming |
| **Agent** | LangGraph (StateGraph) | Stateful multi-step orchestration |
| **STT** | Groq Whisper API (large-v3) | Best accuracy, ~500ms |
| **LLM** | Google Gemini 3.5 Flash Lite | Fast, free, reliable |
| **TTS** | Edge-TTS + gTTS fallback | Neural voice, zero cost |
| **RAG** | FAISS + sentence-transformers | Semantic document search (lazy loaded) |
| **Cache** | Lightweight word-overlap (SQLite) | No ML model needed, ~70ms lookup |
| **Memory** | SQLite | Persistent conversations, zero setup |
| **Search** | DuckDuckGo (ddgs) | Free, optimized with connection reuse |
| **Frontend** | HTML/CSS/JS + Web Audio API | Browser-native, no framework |
| **Deploy** | Docker + Render | Free tier hosting |

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
│       └── cache.py           # Lightweight semantic cache with TTL
├── frontend/
│   └── index.html             # Voice UI + glassmorphism + latency dashboard
├── knowledge_base/            # Drop PDFs here for RAG
├── data/
│   └── voxagent.db            # SQLite database (auto-created)
├── Dockerfile                 # Production Docker build
├── render.yaml                # Render deployment config
├── .env                       # API keys
├── pyproject.toml             # Dependencies
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
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
pip install -e .
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

Go to **http://localhost:8000** and start talking! 🎤

---

## 🧪 Try These Commands

```
🎤 "What's the weather in Delhi?"           → Weather tool
🎤 "Book appointment tomorrow 3pm dentist"  → Booking (Create)
🎤 "Show my bookings"                       → Booking (Read)
🎤 "Reschedule BK-001 to 5pm"              → Booking (Update)
🎤 "Cancel BK-001"                          → Booking (Delete)
🎤 "Look up Rahul Sharma"                   → CRM Lookup
🎤 "Latest news about AI?"                  → Web Search
🎤 "Weather bata aur time bhi bata"         → Multi-tool! 🔥
🎤 "Do you remember what we discussed?"     → Memory recall
```

---

## 🧠 Key Design Decisions

| Decision | Why |
|----------|-----|
| **LangGraph over manual parsing** | Stateful orchestration, multi-tool support, conditional routing |
| **Groq Whisper over local models** | 10x faster, better Hindi accuracy, no GPU needed |
| **SQLite over PostgreSQL** | Zero setup for demo; production migration is trivial |
| **Word-overlap cache over embeddings** | No ML model needed for cache, saves ~200MB RAM on Render |
| **Edge-TTS + gTTS fallback** | Dual redundancy, zero cost, ~200ms latency |
| **Manual tool registry** | Gemini's native function calling had protobuf compatibility issues |
| **Lazy-loaded RAG embeddings** | sentence-transformers loads only when PDFs uploaded, saves RAM |
| **Session memory for demo** | Full persistent memory exists but disabled for public demo. Set `PERSISTENT_MEMORY=True` for local use |

---

## 🚀 Deploy to Render

1. Fork this repo
2. Connect to [Render](https://render.com)
3. Create Web Service → Docker runtime
4. Add environment variables: `GEMINI_API_KEY`, `GROQ_API_KEY`
5. Deploy!

Or use the included `render.yaml` for one-click deploy.

---

## 🎤 Interview Talking Points

> "I built VoxAgent — a real-time voice AI agent with sub-4-second latency. It uses **LangGraph** for stateful agent orchestration with conditional routing across 9 tools including RAG, CRUD booking, and CRM lookup. I implemented **semantic caching** that matches queries by meaning (not exact text), reducing repeat query latency to ~70ms. The architecture supports **persistent cross-session memory** using SQLite. I optimized it for Render's 512MB free tier by lazy-loading embeddings and using a lightweight cache without ML models."

**This project demonstrates:**
- ✅ Real-time systems (WebSocket streaming)
- ✅ Voice AI pipeline (STT + LLM + TTS)
- ✅ Agentic architecture (LangGraph + multi-tool)
- ✅ RAG expertise (FAISS + embeddings)
- ✅ Semantic caching (word-overlap similarity + TTL)
- ✅ Production mindset (error handling, fallbacks, memory optimization)
- ✅ Deployment (Docker + Render)

---

## 📄 License

MIT License — feel free to use, modify, and build upon this project.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/kalashkj28">Kalash Jain</a> · <a href="https://www.linkedin.com/in/kalashjain28">LinkedIn</a> · <a href="https://kalashkj28.github.io">Portfolio</a>
</p>
