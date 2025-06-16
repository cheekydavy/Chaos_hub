FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and outputs
RUN mkdir -p /app/static/Uploads /app/static/outputs

# Set environment variables
ENV FLASK_ENV=production \
    PORT=8080 \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run gunicorn with eventlet
CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:8080", "--log-level", "info", "app:app"]
