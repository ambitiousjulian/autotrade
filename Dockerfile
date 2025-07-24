# Python backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY backtest/ ./backtest/

# Create necessary directories
RUN mkdir -p /app/core/data /app/core/models /app/reports

# Create empty __init__.py files
RUN touch /app/core/__init__.py /app/backtest/__init__.py

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8000

# Start with watcher
CMD ["python", "-m", "core.watcher"]