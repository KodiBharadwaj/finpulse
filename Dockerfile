# FinPulse Environment - HuggingFace Space Dockerfile
# Simplified for competition submission
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY src/envs/finpulse_env/server/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY src/ /app/src/

# Set Python path so imports work correctly
ENV PYTHONPATH=/app

# Expose port 8000 (HuggingFace Spaces will map this)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "src.envs.finpulse_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
