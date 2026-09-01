FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -e .

# Copy source code
COPY app/ app/
COPY frontend/ frontend/

# Create directories
RUN mkdir -p data knowledge_base

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/')" || exit 1

# Run server
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
