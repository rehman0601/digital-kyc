# Phase 3: Docker
# Simple, single-stage Dockerfile -> easy to explain in viva:
# base image -> copy code -> install deps -> run with gunicorn

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching - if requirements.txt
# doesn't change, Docker reuses this layer on rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Folder for uploaded KYC documents
RUN mkdir -p uploads logs

EXPOSE 5000

# Use gunicorn (production WSGI server) instead of Flask's dev server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
