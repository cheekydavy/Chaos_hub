FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    build-essential \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static/Uploads /app/static/outputs \
 && chmod -R 777 /app/static

ENV FLASK_ENV=production \
    PORT=8000 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:8080", "--log-level", "info", "app:app"]
