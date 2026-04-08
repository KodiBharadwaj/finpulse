FROM python:3.10-slim

WORKDIR /app

# Install CA certificates for SSL
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY envs/finpulse_env/server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy core OpenEnv modules
COPY core /app/core

# Copy FinPulse environment
COPY envs/finpulse_env /app/envs/finpulse_env

# Set Python path so imports work
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run server from correct directory
WORKDIR /app/envs/finpulse_env/server

CMD ["python", "app.py"]
