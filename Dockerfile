FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for SQLite vector extensions if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY tests/ tests/

# Set env vars
ENV PYTHONPATH=/app
ENV MEMORY_SYSTEM_CONFIG=/app/config.json

# Default to REST API server
EXPOSE 8000

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
