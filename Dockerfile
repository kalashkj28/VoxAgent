FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy everything
COPY pyproject.toml ./
COPY app/ app/
COPY frontend/ frontend/

# Create directories
RUN mkdir -p data knowledge_base

# Install dependencies
RUN uv pip install --system "ddgs>=9.16.0" "edge-tts==6.1.12" "faiss-cpu>=1.15.0" "fastapi==0.115.0" "google-generativeai==0.8.0" "gtts>=2.5.4" "httpx>=0.28.1" "langchain-core>=1.6.1" "langgraph>=1.2.2" "pypdf>=6.16.2" "python-dotenv==1.0.1" "python-multipart==0.0.9" "sentence-transformers>=6.0.0" "uvicorn==0.30.0" "websockets==12.0"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/')" || exit 1

# Run server
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
