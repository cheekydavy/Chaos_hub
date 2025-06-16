FROM python:3.13.0-slim-bookworm

WORKDIR /app

# Install minimal dependencies
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for file storage
RUN mkdir -p /app/Uploads /app/outputs

# Set environment variables
ENV FLASK_ENV=production \
    PORT=8080

# Expose port
EXPOSE 8080

# Run gunicorn with eventlet
CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:8080", "app:app"]